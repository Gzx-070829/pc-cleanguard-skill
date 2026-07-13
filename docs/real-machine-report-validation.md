# Real Machine Report Validation

只把已经由用户显式提供、并在本地去标识化的 report 交给验证器：

```powershell
python -m pc_cleanguard.cli validate report --input report.json --output .pcg-validation
```

输出包含 report 形状、PII 去标识化清单、matchability、未支持字段和下一步。验证器不上传、不联网、不读取额外文件、不修改系统。`matchability_score` 只表示元数据是否足以供人工复核，不表示风险或执行许可。
