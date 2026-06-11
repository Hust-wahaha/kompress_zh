# HF Adapter Export TODO: baseline v1

当前仓库已经把 HF 首发叙事、license、上传形态和 README 全部准备好了。

现在真正还差的是：**把实际的 LoRA adapter 导出文件拿到本地并放入 HF release staging 目录。**

## Current Local Situation

目前本地仓库已确认：

- 有训练摘要
  - `experiments/remote_sync/20260610_152155_train_standardset_v6_1234_qwen3.5-0.8b_reference_v1__train_summary.json`
- 有评测摘要
  - `experiments/remote_sync/20260610_160737_eval_standardset_v6_1234_qwen3.5-0.8b_reference_v1_test_eval__eval_summary_full.json`
- 但当前工作树里**没有发现**现成的：
  - `adapter_config.json`
  - `adapter_model.safetensors`

这说明：

- 要么实际 adapter 文件还在远端训练机
- 要么还没有同步回当前仓库

## Target Staging Directory

HF 首发本地 staging 目录已创建：

- [hf_release/baseline_v1_lora/README.md](../hf_release/baseline_v1_lora/README.md)
- [hf_release/baseline_v1_lora/NOTICE.md](../hf_release/baseline_v1_lora/NOTICE.md)

最终应补入：

- `adapter_config.json`
- `adapter_model.safetensors`

## Minimum Next Step

从真实训练输出中取回 `reference_v1 / checkpoint-61` 对应的 LoRA adapter 文件，并放到：

```text
hf_release/baseline_v1_lora/
```

## After Adapter Files Arrive

拿到真实文件后，按这个顺序执行：

1. 检查文件名是否为：
   - `adapter_config.json`
   - `adapter_model.safetensors`
2. 检查 README 中的 adapter repo 名称是否需要改成最终 HF repo 名称
3. 将该目录作为 HF model repo 初始内容上传
4. 上传后验证 README 展示与示例代码
