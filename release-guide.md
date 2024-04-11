## Releasee flow guide for ForumAISDK

### Requirements
- Python >= 3.8

### Steps
You can find the offical guide from here https://packaging.python.org/en/latest/tutorials/packaging-projects/

1. Clean the `dist` if have any
```
rm dist/*
```
2. Build the package
```
python3 -m build
```
3. Install twine for uploading packgage (Skip if already installed)
```
pip install twine
```

3 Upload to PyPi
```
python3 -m twine upload dist/*
```
Once the the above command is executed then you need to enter the PyPi key of your account and then the uploading process will be in progress.
