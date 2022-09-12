from typing import Union, Any, get_type_hints
import pytest
from typed_params import (
    BaseModel,
    load_params_dict_from_json_file,
    raise_error_with_location,
)


class MockSubObject(BaseModel):
    STRING_1: str


class MockParams(BaseModel):
    TEST_STRING: str
    TEST_INT: int
    TEST_DICT: dict
    TEST_LIST: list
    TEST_SUBOBJECT: MockSubObject


@pytest.fixture
def params_dict():
    return load_params_dict_from_json_file("./tests/test_data/mock_params.json")


@pytest.fixture
def mock_params(params_dict) -> MockParams:
    return MockParams(params_dict)


def test_params_correctly_sets_basic_types(mock_params, params_dict):
    assert mock_params.TEST_STRING == params_dict["TEST_STRING"]
    assert mock_params.TEST_INT == params_dict["TEST_INT"]
    assert mock_params.TEST_DICT == params_dict["TEST_DICT"]
    assert mock_params.TEST_LIST == params_dict["TEST_LIST"]


def test_params_to_dict(mock_params):
    actual_dict = mock_params.to_dict()
    expected_dict = {
        "TEST_STRING": "TEST_STRING",
        "TEST_INT": "TEST_INT",
        "TEST_DICT": {"TEST_DICT_1": "1"},
        "TEST_LIST": ["1", "2", "3"],
        "TEST_SUBOBJECT": MockSubObject({"STRING_1": "some_string"}),
    }

    assert actual_dict == expected_dict


def test_params_str_method(mock_params):
    assert "(MockParams Location: > MockParams)" == str(mock_params)


def test_params_repr_method(mock_params):
    assert "(MockParams Location: > MockParams)" == repr(mock_params)


def test_params_equality(mock_params, params_dict):
    assert mock_params == MockParams(params_dict)


def test_params_inequality(mock_params, params_dict):
    params_dict["TEST_STRING"] = "NEW_STRING"
    assert mock_params != MockParams(params_dict)


def test_subclass_inequality(mock_params, params_dict):
    class ClassWithSameAttributes(BaseModel):
        TEST_STRING: str
        TEST_INT: int
        TEST_DICT: dict
        TEST_LIST: list
        TEST_SUBOBJECT: MockSubObject

    assert mock_params != ClassWithSameAttributes(params_dict)


def test_check_param_being_loaded_is_in_type_definition_raises_error(
    mock_params: MockParams,
):
    param_name = "NOT_IN_TYPE_DEFINITION"

    with pytest.raises(ValueError) as err:
        mock_params._check_param_being_loaded_is_in_type_definition(param_name)

    assert param_name in str(err.value)
    assert "Location: > MockParams" in str(err.value)


def test_init_with_no_attributes_raises_error(params_dict: dict[str, Any]):
    class ClassWithNoAttributes(BaseModel):
        pass

    with pytest.raises(ValueError) as err:
        ClassWithNoAttributes(params_dict)

    assert (
        "Class definition for ClassWithNoAttributes does not contain any attributes!"
        in str(err.value)
    )


def test_init_subobject_with_no_attributes_raises_error():
    class ClassWithNoAttributes(BaseModel):
        pass

    class ClassWithSubObjectWithNoAttributes(BaseModel):
        SUBOBJECT_WITH_NO_ATTRIBUTES: ClassWithNoAttributes

    class_with_subobject_dict = {"SUBOBJECT_WITH_NO_ATTRIBUTES": {}}

    with pytest.raises(ValueError) as err:
        ClassWithSubObjectWithNoAttributes(class_with_subobject_dict)

    assert (
        "Class definition for ClassWithNoAttributes does not contain any attributes!"
        in str(err.value)
    )


def test_check_param_being_loaded_is_in_type_definition_for_subobject_raises_error(
    params_dict: dict[str, Any]
):
    invalid_subobject_dict = {"NOT_IN_TYPE_DEFINITION": "some_string"}

    params_dict["TEST_SUBOBJECT"] = invalid_subobject_dict
    with pytest.raises(ValueError) as err:
        MockParams(params_dict)

    assert "Location: > MockParams > MockSubObject" in str(err.value)


def test_check_param_being_loaded_is_in_type_definition_for_list_of_subobject_raises_error():
    class ClassWithListOfSubObjects(BaseModel):
        LIST_SUBOBJECTS: list[MockSubObject]

    invalid_subobject_list_params = {
        "LIST_SUBOBJECTS": [
            {"STRING_1": "some_string"},
            {"NOT_IN_TYPE_DEFINITION": "some_string"},
            {"STRING_1": "some_string"},
        ]
    }

    with pytest.raises(ValueError) as err:
        ClassWithListOfSubObjects(invalid_subobject_list_params)

    assert (
        "Location: > ClassWithListOfSubObjects > LIST_SUBOBJECTS > Element 1 > MockSubObject"
        in str(err.value)
    )


def test_check_param_being_loaded_is_in_type_definition_for_dict_of_subobject_raises_error():
    class ClassWithListOfSubObjects(BaseModel):
        DICT_SUBOBJECTS: dict[str, MockSubObject]

    invalid_subobject_list_params = {
        "DICT_SUBOBJECTS": {"SUBOBJECT_1": {"NOT_IN_TYPE_DEFINITION": "some_string"}}
    }

    with pytest.raises(ValueError) as err:
        ClassWithListOfSubObjects(invalid_subobject_list_params)

    assert (
        "Location: > ClassWithListOfSubObjects > DICT_SUBOBJECTS > Key SUBOBJECT_1 > MockSubObject"
        in str(err.value)
    )


def test_convert_typed_subparams_to_objects_for_singular_subobject(
    mock_params: MockParams,
):
    class ClassWithSubObjectParam:
        SUBOBJECT: MockSubObject

    type_hints_by_param_name = get_type_hints(ClassWithSubObjectParam)
    param_name = list(type_hints_by_param_name.keys())[0]
    param_value = {"STRING_1": "some_string"}

    expected_result = MockSubObject(param_value)

    actual_result = mock_params._convert_typed_subparams_to_objects(
        type_hints_by_param_name, param_name, param_value
    )

    assert expected_result == actual_result


def test_convert_typed_subparams_to_objects_for_list_of_subobjects(
    mock_params: MockParams,
):
    class ClassWithListOfSubObjectParam:
        SUBOBJECT_LIST: list[MockSubObject]

    type_hints_by_param_name = get_type_hints(ClassWithListOfSubObjectParam)
    param_name = list(type_hints_by_param_name.keys())[0]
    subobject_value1 = {"STRING_1": "some_string"}
    subobject_value2 = {"STRING_1": "some_other_string"}
    param_value = [subobject_value1, subobject_value2]

    expected_result = [
        MockSubObject(subobject_value1),
        MockSubObject(subobject_value2),
    ]

    actual_result = mock_params._convert_typed_subparams_to_objects(
        type_hints_by_param_name, param_name, param_value
    )

    assert expected_result == actual_result


def test_convert_typed_subparams_to_objects_for_dict_of_subobject(
    mock_params: MockParams,
):
    class ClassWithDictOfSubObjectParam:
        SUBOBJECT_DICT: dict[str, MockSubObject]

    type_hints_by_param_name = get_type_hints(ClassWithDictOfSubObjectParam)
    param_name = list(type_hints_by_param_name.keys())[0]
    subobject_value = {"STRING_1": "some_string"}
    param_value = {"subobject": subobject_value}

    expected_result = {"subobject": MockSubObject(subobject_value)}

    actual_result = mock_params._convert_typed_subparams_to_objects(
        type_hints_by_param_name, param_name, param_value
    )

    assert expected_result["subobject"] == actual_result["subobject"]


def test_should_do_list_conversion_handles_complex_types(mock_params: MockParams):
    type_origin = list
    type_args = [Union[str, int]]

    assert not mock_params._should_do_list_conversion(type_origin, type_args)


def test_should_do_list_conversion(mock_params: MockParams):
    type_origin = list
    type_args = [MockSubObject]

    assert mock_params._should_do_list_conversion(type_origin, type_args)


def test_do_list_conversion_raises_error(mock_params: MockParams):
    type_origin = list
    type_args = [MockSubObject]
    param_value = {"STRING_1": "some_string"}
    param_name = "MOCK_SUB_OBJECT"
    with pytest.raises(ValueError) as err:
        mock_params._do_list_conversion(type_origin, type_args, param_value, param_name)

    assert (
        "Type hint and value do not match for MOCK_SUB_OBJECT with value {'STRING_1': 'some_string'} with type <class 'dict'> should be <class 'list'>"
        in str(err.value)
    )
    assert "Location: > MockParams" in str(err.value)


def test_should_not_do_list_conversion(mock_params: MockParams):
    type_origin = list
    type_args = [str]

    assert not (mock_params._should_do_list_conversion(type_origin, type_args))


def test_should_do_dict_conversion(mock_params: MockParams):
    type_origin = dict
    type_args = [str, MockSubObject]

    assert mock_params._should_do_dict_conversion(type_origin, type_args)


def test_should_do_dict_conversion_handles_complex_types(mock_params: MockParams):
    type_origin = dict
    type_args = [str, Union[str, int]]

    assert not mock_params._should_do_dict_conversion(type_origin, type_args)


def test_do_dict_conversion_raises_error(mock_params: MockParams):
    type_origin = dict
    type_args = [str, MockSubObject]
    param_value = [{"mock_sub_object": {"STRING_1": "some_string"}}]
    param_name = "SOME_PARAM"
    with pytest.raises(ValueError) as err:
        mock_params._do_dict_conversion(type_origin, type_args, param_value, param_name)

    assert (
        "Type hint and value do not match for SOME_PARAM with value [{'mock_sub_object': {'STRING_1': 'some_string'}}] with type <class 'list'> should be <class 'dict'>"
        in str(err.value)
    )
    assert "Location: > MockParams" in str(err.value)


def test_should_not_do_dict_conversion(mock_params: MockParams):
    type_origin = dict
    type_args = [str, str]

    assert not mock_params._should_do_dict_conversion(type_origin, type_args)


def test_raise_error_with_location():
    error_to_raise = ValueError
    error_message = "Error message without location"
    location = " > some location"
    with pytest.raises(ValueError) as err:
        raise_error_with_location(error_to_raise, error_message, location)

    assert error_message in str(err.value)
    assert location in str(err.value)
