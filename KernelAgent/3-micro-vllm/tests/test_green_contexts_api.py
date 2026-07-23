import torch
import sys

print("CUDA Version:", torch.version.cuda)
print("PyTorch Version:", torch.version.device if hasattr(torch.version, "device") else torch.__version__)

# 1. Test PyTorch GreenContext API
try:
    from torch.cuda.green_contexts import GreenContext
    print("✅ torch.cuda.green_contexts is importable!")
    try:
        ctx = GreenContext.create(num_sms=16)
        print("✅ GreenContext.create(num_sms=16) succeeded!")
        ctx.set_context()
        print("✅ ctx.set_context() succeeded!")
        ctx.pop_context()
        print("✅ ctx.pop_context() succeeded!")
    except Exception as e:
        print(f"❌ GreenContext creation or activation failed: {e}")
except ImportError as e:
    print(f"❌ torch.cuda.green_contexts is not importable: {e}")

# 2. Test cuda.core API
try:
    from cuda import cuda
    from cuda.core import Device, ContextOptions, SMResourceOptions
    print("✅ cuda.core module is importable!")
    try:
        # Initialize cuda driver
        cuda.cuInit(0)
        dev = Device(0)
        sm = dev.resources.sm
        print(f"✅ Device found: {dev.name}, total SMs: {sm.sm_count}")
        
        # Test split
        if sm.sm_count >= 16:
            long_grp, crit_grp = sm.split(SMResourceOptions(count=(sm.sm_count - 16, 16)))[0]
            print(f"✅ SM split succeeded: long_grp={long_grp}, crit_grp={crit_grp}")
            
            ctx_crit = dev.create_context(ContextOptions(resources=[crit_grp]))
            print("✅ dev.create_context succeeded!")
            
            ctx_crit.push_current()
            print("✅ ctx_crit.push_current succeeded!")
            ctx_crit.pop_current()
            print("✅ ctx_crit.pop_current succeeded!")
        else:
            print(f"⚠️ GPU has too few SMs ({sm.sm_count}) to split.")
    except Exception as e:
        print(f"❌ cuda.core operations failed: {e}")
except ImportError as e:
    print(f"❌ cuda.core module is not importable: {e}")
