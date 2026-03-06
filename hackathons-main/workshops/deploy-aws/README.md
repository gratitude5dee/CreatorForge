# Deploy AI Agents to AWS Fargate with Nevermined Payments

Deploy a **seller** and **buyer** A2A agent pair to AWS Fargate with Nevermined x402 payment integration. All LLM inference uses **Amazon Bedrock** (no OpenAI key needed).

## Architecture

```
Buyer Agent (Fargate)          Seller Agent (Fargate)
  - Bedrock Nova Pro             - Bedrock Nova Pro
  - Web UI + SSE streaming       - A2A server + tools
  - PaymentsClient (x402)        - PaymentsA2AServer (x402)
         |                              |
         +--- ALB :8000     ALB :9000 --+
                   \         /
                    Internet
```

The **seller** exposes tools (search, summarize, research) behind Nevermined payment protection. The **buyer** discovers the seller, generates x402 payment tokens, and purchases data on behalf of users.

## Prerequisites

- **AWS CLI** configured with credentials (`aws configure`)
- **Docker** running locally
- **Nevermined account** at [nevermined.app](https://nevermined.app) with:
  - A seller API key and a buyer API key
  - A payment plan (credit-based) with plan ID and agent ID

### Get Nevermined Credentials

1. Sign in at [nevermined.app](https://nevermined.app)
2. Go to **API Keys** > **Global NVM API Keys** > **+ New API Key**
3. Create two keys: one for the seller (builder), one for the buyer (subscriber)
4. Create a payment plan and note the `planId` and `agentId`

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/nevermined-io/hackathons.git
cd hackathons/workshops/deploy-aws

cp .env.example .env
# Edit .env with your credentials:
#   SELLER_NVM_API_KEY, BUYER_NVM_API_KEY, NVM_PLAN_ID, NVM_AGENT_ID
```

### 2. Deploy

```bash
./deploy-fargate.sh
```

This single script handles everything:
- Creates ECR repositories and pushes Docker images
- Creates ALBs with health-checked target groups
- Registers ECS task definitions with Bedrock access
- Deploys Fargate services

Deployment takes ~3 minutes. At the end you'll see:

```
======================================
  Deployment Complete
======================================

  Seller: http://nvm-seller-alb-XXXXXXXXX.us-west-2.elb.amazonaws.com:9000
  Buyer:  http://nvm-buyer-alb-XXXXXXXXX.us-west-2.elb.amazonaws.com:8000
  Model:  us.amazon.nova-pro-v1:0
```

### 3. Test

```bash
# Check seller agent card
curl $SELLER_URL/.well-known/agent.json

# Check buyer health
curl $BUYER_URL/ping

# Run a paid query (buyer discovers seller, pays with x402, gets results)
curl -X POST $BUYER_URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Search for Python programming language"}'
```

### 4. View logs

```bash
aws logs tail /ecs/nvm-seller-agent --follow --region us-west-2
aws logs tail /ecs/nvm-buyer-agent --follow --region us-west-2
```

## How It Works

1. **Buyer** receives a user query via `/api/chat` (SSE streaming)
2. Buyer's Bedrock agent calls `discover_agent` to fetch the seller's agent card
3. Buyer calls `purchase_a2a` which:
   - Generates an x402 access token via `PaymentsClient`
   - Sends an A2A JSON-RPC message with `payment-signature` header
4. **Seller's** `PaymentsA2AServer` verifies the payment token
5. Seller's Bedrock agent runs tools (search, summarize, research) and responds
6. Response streams back to the buyer and out to the user

## Seller Tools

| Tool | Credits | Description |
|------|---------|-------------|
| `search_data` | 1 | Web search via DuckDuckGo |
| `summarize_data` | 5 | LLM-powered content summarization |
| `research_data` | 10 | Multi-step research pipeline |

## Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SELLER_NVM_API_KEY` | Yes | - | Seller's Nevermined API key |
| `BUYER_NVM_API_KEY` | Yes | - | Buyer's Nevermined API key |
| `NVM_PLAN_ID` | Yes | - | Payment plan ID |
| `NVM_AGENT_ID` | Yes | - | Seller agent ID |
| `NVM_ENVIRONMENT` | No | `sandbox` | Nevermined environment |
| `AWS_REGION` | No | `us-west-2` | AWS region |
| `BEDROCK_MODEL_ID` | No | `us.amazon.nova-pro-v1:0` | Bedrock model |
| `CLUSTER_NAME` | No | `nvm-agents` | ECS cluster name |

## Cleanup

To tear down all AWS resources:

```bash
AWS_REGION=us-west-2
CLUSTER=nvm-agents

# Delete services
aws ecs update-service --cluster $CLUSTER --service nvm-seller-svc --desired-count 0 --region $AWS_REGION
aws ecs update-service --cluster $CLUSTER --service nvm-buyer-svc --desired-count 0 --region $AWS_REGION
aws ecs delete-service --cluster $CLUSTER --service nvm-seller-svc --force --region $AWS_REGION
aws ecs delete-service --cluster $CLUSTER --service nvm-buyer-svc --force --region $AWS_REGION

# Delete ALBs (listeners auto-delete)
for name in nvm-seller-alb nvm-buyer-alb; do
  ARN=$(aws elbv2 describe-load-balancers --names $name --region $AWS_REGION --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null)
  [ "$ARN" != "None" ] && aws elbv2 delete-load-balancer --load-balancer-arn $ARN --region $AWS_REGION
done

# Delete target groups
for name in nvm-seller-alb-tg nvm-buyer-alb-tg; do
  ARN=$(aws elbv2 describe-target-groups --names $name --region $AWS_REGION --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null)
  [ "$ARN" != "None" ] && aws elbv2 delete-target-group --target-group-arn $ARN --region $AWS_REGION
done

# Delete cluster, ECR, logs
aws ecs delete-cluster --cluster $CLUSTER --region $AWS_REGION
aws ecr delete-repository --repository-name nvm-seller-agent --force --region $AWS_REGION
aws ecr delete-repository --repository-name nvm-buyer-agent --force --region $AWS_REGION
aws logs delete-log-group --log-group-name /ecs/nvm-seller-agent --region $AWS_REGION
aws logs delete-log-group --log-group-name /ecs/nvm-buyer-agent --region $AWS_REGION
```

Security groups (`nvm-seller-sg`, `nvm-buyer-sg`) can be deleted after ALB ENIs finish draining (~1-2 minutes after ALB deletion).
