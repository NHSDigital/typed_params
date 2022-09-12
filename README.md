# typed_params

This package handles the processing of a params JSON files. It will check the type hints in any class that extends from `BaseModel` and convert the JSON object into the relevant class. This means that these subobjects in params can be accessed in the same way as params.

**_For any queries please email enquiries@nhsdigital.nhs.uk_**

## Params

A params JSON file should contain configuration that is likley to change within your publication. For example, in a yearly run publication, the configuration for 2020 could be different for 2021. Having multiple JSON files for each year allows for the program to run for new years of configuration but with no impact on testing. _This is important as a publication's methodology is complicated and it would be difficult to change the tests for each new year._

### Example Usage

First you must create a class that inherits from `BaseModel`. Create attributes that you require for your params. **These must have type hints.**

```python
class ExampleParams(BaseModel):
  PUBLICATION_YEAR: str
  PUBLICATION_ROW_ORDER: list[str]
```

You can then instantiate the class and pass in a dictionary of param values.

```python
params_dict = {
  "PUBLICATION_YEAR": 2022,
  "PUBLICATION_ROW_ORDER": [
    "ROW_1",
    "ROW_2",
    "ROW_3"
  ]
}

params = ExampleParams(params_dict)
```

Now the `params` variable will autocomplete for all of it's attributes and have correct typing. This makes it a lot easier to use params.

```python
print(params_dict["PUBLICATION_YEAR"])
for row in params_dict["PUBLICATION_ROW_ORDER"]:
  print(row)
```

becomes

```python
print(params.PUBLICATION_YEAR) # 2022
for row in params.PUBLICATION_ROW_ORDER:
  print(row) # ROW_1, ROW_2 and then ROW_3
```

This package becomes more powerful when using sub-objects. This allows for easier access of complex params.

```python
class ExampleParamsRowNames(BaseModel):
  TOTAL_ROW: str
  QUESTION_ROW: str


class ExampleParamsWithSubObject(BaseModel):
  ROW_NAMES: ExampleParamsRowNames

complicated_params_dict = {
    "ROW_NAMES": {
      "TOTAL_ROW": "total_row_name",
      "QUESTION_ROW": "question_row_name"
    }
}

params = ExampleParamsWithSubObject(complicated_params_dict)
```

Without using the `BaseModel` class, to access `TOTAL_ROW` you would have to do the following.

```python
print(complicated_params_dict["ROW_NAMES"]["TOTAL_ROW"])
```

Which can be prone to errors if you type the names wrong.
Using the `BaseModel` class and creating a params object makes access this kind of nested accessing a lot easier.

```python
print(params.ROW_NAMES.TOTAL_ROW) # total_row_name
```

This same principle can be applied with lists and dictionaries of sub-objects.

### Suggested Usage for a Publication

In the base `__init__.py` file of your project create a variable `params`. Load in your JSON params file. Create an instance of your subclass and pass in the loaded JSON data. You can assign the instance to the `params` variable.

```python
# __init__.py
params_dict = load_params_dict_from_json_file(PARAMS_JSON_TO_USE)
params = ExampleParams(params_dict)
```

This ensures that params can be imported anywhere in your project using:

```python
from YOUR_PROJECT_NAME import params
```

This will mean that your params are fixed to whichever JSON file you choose to use in the `__init__.py` file. However, you can set new params by using the method `set_params_from_params_dict`. You may want to do this if you want to give your user the option to run your program with different params files.

```python
user_input = input("Which params file would you like to use?: ")
new_params_dict = load_params_dict_from_json_file(user_input)
params.set_params_from_params_dict(new_params_dict)
```

You will now have to access your params from within a function or params will contain values from the previous params JSON file. This is because Python will evaluate all global variables before running the program. As such, the params in `__init__.py` will be evaluated first and then everywhere in the code in the global scope will have that same value. These variables are not re-evaluated if you change the value of params. If you access the params within a function then the value will be evaluated when the function is run. Therefore, you can change the value of params in your entry point code and any subsequent accessing of params will have the correct value.

## Working on the code

**_Please update the changelog with any work that you do on this package!_**

### Development Setup - Virtual Environment and Git Hook

If you are going to work on this package, please carry out the following development setup steps.

Run the following command to set up your environment correctly from the root directory (the top level `typed_params` folder).

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r dev-requirements.txt
python .\git-hooks\setup-hooks.py
```

For Visual Studio Code it is necessary that you change your default interpreter to the virtual environment you just created `.venv`. To do this use the shortcut `Ctrl-Shift-P`, search for `Python: Select interpreter` and select `.venv` from the list.

**Please do not use the VS Code Git Tab to commit as this will no longer work.**

_However, you can use it for adding files to be committed._

### Changing the installed packages

If, while developing this package, you change the installed packages, please update the environment file using

```
pip freeze > dev-requirements.txt
```

## Testing the code

You can run the tests on the repository using (from the base directory)

```
pytest
```
