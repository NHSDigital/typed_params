from typing import Any, Union, get_type_hints, get_origin, get_args, Type
from pathlib import Path
import json


def load_params_dict_from_json_file(file_path: Union[str, Path]) -> dict[str, Any]:
    with open(file_path) as params_file:
        return json.load(params_file)


def raise_error_with_location(
    error: Type[Exception], error_message: str, location: str
) -> None:
    raise error(f"{error_message} Location:{location}")


class BaseModel:
    def __init__(self, params_dict: dict[str, Any], location_tracker: str = "") -> None:
        location_tracker += f" > {type(self).__name__}"
        self._location_tracker = location_tracker
        self.set_params_from_params_dict(params_dict)

    def __eq__(self, other: object) -> bool:
        """
        Two instances of BaseModel are equal if:
        - they are of the same type
        - their public facing attributes are the same and have the same values.
        """
        return type(self) == type(other) and self.to_dict() == other.to_dict()

    def __str__(self) -> str:
        return f"({type(self).__name__} Location:{self._location_tracker})"

    def __repr__(self) -> str:
        return str(self)

    def to_dict(self):
        """
        Returns a dict that does not include private attributes
        This does not convert subobjects to dicts even if they extend from BaseModel
        """
        dict_with_private_variables = vars(self).copy()
        del dict_with_private_variables["_location_tracker"]
        return dict_with_private_variables

    def set_params_from_params_json_file(self, file_path: Union[str, Path]):
        """
        Set all params from a json file and verify
        """
        params_dict = load_params_dict_from_json_file(file_path)
        self.set_params_from_params_dict(params_dict)

    def set_params_from_params_dict(self, params_dict: dict[str, Any]) -> None:
        """
        This function sets all params from a dictionary and verifies that they are correct
        """
        self._set_attributes_from_params_dict(params_dict)
        self._check_params_object_has_all_attributes_in_type_definition()
        self.run_validations()

    def run_validations(self) -> None:
        """
        This function should be overridden to perform any validations
        of the params you have implemented
        """
        pass

    def _set_attributes_from_params_dict(self, params_dict: dict[str, Any]) -> None:
        """
        This is a private function that sets the params without verification
        """
        try:
            type_hints_by_param_name = get_type_hints(self)
        except TypeError:
            raise ValueError(
                f"Class definition for {type(self).__name__} does not contain any attributes!"
            )
        for param_name, param_value in params_dict.items():
            self._check_param_being_loaded_is_in_type_definition(param_name)
            result = self._convert_typed_subparams_to_objects(
                type_hints_by_param_name, param_name, param_value
            )
            setattr(self, param_name, result)

    def _convert_typed_subparams_to_objects(
        self,
        type_hints_by_param_name: dict[str, Any],
        param_name: str,
        param_value: Any,
    ) -> Any:
        """
        This function will convert subparams to objects
        It will also convert lists of subparams and also dicts of subparams

        e.g

        param_name: list[SubClassOfBaseModel] -> Will convert each object in the list
                                                 to an instance of SubClassOfBaseModel
        """
        type_hint = type_hints_by_param_name[param_name]
        type_origin = get_origin(type_hint)
        if type_origin is None:
            type_origin = type_hint
        type_args = get_args(type_hint)

        result = param_value

        if issubclass(type_origin, BaseModel):
            result = type_origin(param_value, location_tracker=self._location_tracker)

        if self._should_do_list_conversion(type_origin, type_args):
            result = self._do_list_conversion(
                type_origin, type_args, param_value, param_name
            )

        if self._should_do_dict_conversion(type_origin, type_args):
            result = self._do_dict_conversion(
                type_origin, type_args, param_value, param_name
            )
        return result

    def _should_do_list_conversion(
        self, type_origin: Type[Any], type_args: tuple[Type[Any]]
    ) -> bool:
        return (
            type_origin is list
            and type_args
            and get_origin(type_args[0]) is None
            and issubclass(type_args[0], BaseModel)
        )

    def _do_list_conversion(
        self,
        type_origin: Type[Any],
        type_args: tuple[Type[Any]],
        param_value: Any,
        param_name: str,
    ) -> list[Any]:
        type_hint_and_value_do_not_match = (
            type_origin is list and type(param_value) is not list
        )
        if type_hint_and_value_do_not_match:
            raise_error_with_location(
                ValueError,
                f"Type hint and value do not match for {param_name} with value {param_value} with type {type(param_value)} should be {type_origin}",
                self._location_tracker,
            )
        return [
            type_args[0](
                item,
                location_tracker=f"{self._location_tracker} > {param_name} > Element {i}",
            )
            for i, item in enumerate(param_value)
        ]

    def _should_do_dict_conversion(
        self, type_origin: Type[Any], type_args: tuple[Type[Any]]
    ) -> bool:
        return (
            type_origin is dict
            and len(type_args) == 2
            and get_origin(type_args[1]) is None
            and issubclass(type_args[1], BaseModel)
        )

    def _do_dict_conversion(
        self,
        type_origin: Type[Any],
        type_args: tuple[Type[Any]],
        param_value: Any,
        param_name: str,
    ) -> dict[str, Any]:
        type_hint_and_value_do_not_match = (
            type_origin is dict and type(param_value) is not dict
        )
        if type_hint_and_value_do_not_match:
            raise_error_with_location(
                ValueError,
                f"Type hint and value do not match for {param_name} with value {param_value} with type {type(param_value)} should be {type_origin}",
                self._location_tracker,
            )
        return {
            key: type_args[1](
                value,
                location_tracker=f"{self._location_tracker} > {param_name} > Key {key}",
            )
            for key, value in param_value.items()
        }

    def _check_params_object_has_all_attributes_in_type_definition(self) -> None:
        for attribute_name in self.__annotations__:
            if not hasattr(self, attribute_name):
                raise_error_with_location(
                    ValueError,
                    f"""
The attribute {attribute_name} is missing from the params object
Even after the params have been loaded.
Please check it is in the params.json file you have selected.
""",
                    location=self._location_tracker,
                )

    def _check_param_being_loaded_is_in_type_definition(self, param_name) -> None:
        if not (param_name in self.__annotations__):
            raise_error_with_location(
                ValueError,
                f"""
You are trying to set the attribue {param_name} in the Params object, but it is not listed in the Params object.
Check the params.json file does not have a spelling error.
If you are adding a new param to the params json, please add a type definition in your Params class.
""",
                location=self._location_tracker,
            )
