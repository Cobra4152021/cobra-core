# KC-002 Cloud Runbook

## 1. Rent GPU

- Prefer A6000 48GB / L40S 48GB / A100 40GB  
- Accept 4090/3090 24GB if cheaper  
- Cap: **$2.50/hr**, **8 hours**, **$100** total  
- Ensure **≥100GB** disk  

## 2. Bootstrap

```bash
git clone https://github.com/Cobra4152021/cobra-core.git
cd cobra-core
git checkout kc-002-real-weight-validation

# CUDA PyTorch (example)
pip install torch --index-url https://download.pytorch.org/whl/cu124

cd kc002
cp .env.example .env
# set HF_HOME to large disk, e.g. /workspace/hf
make setup
make validate-env   # MUST exit 0
```

## 3. Execute gates (stop on failure)

```bash
make text-baseline
make siglip
make forward        # mandatory
make overfit
make dependence
make regression
make moe
```

## 4. Sync artifacts then destroy instance

```bash
# copy artifacts/experiments + docs updates
# verify checksums
# terminate GPU instance immediately
```

## 5. Do not

- Leave the pod idle  
- Download LLaVA / Infinity-MM  
- Merge LoRA into base during KC-002  
- Point production Cobra at the endpoint  
