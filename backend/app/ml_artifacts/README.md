# ML Artifacts

Place trained model files here (e.g. `fraud_xgb_model.json` exported via
`XGBClassifier.save_model()`). This directory is gitignored for the actual
model binaries — only `.gitkeep` is tracked. In production, prefer pulling
the model artifact from S3 / a model registry at container startup instead of
baking it into the image, so you can update the model without rebuilding.
