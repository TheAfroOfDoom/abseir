"""
Defines how simulation views interact with simulation models, in addition to:

* gracefully handling unique constraint violations (400 Bad Request)
"""
from copy import copy
from typing import Generic, TypeVar

from django.db import IntegrityError
from rest_framework import serializers, validators

from .models import Data, Instance, Parameters, Population, Sample


M = TypeVar("M")


class _SimulationSerializer(serializers.ModelSerializer, Generic[M]):
    """Abstract simulation model serializer that provides common behavior:
    * defines common exposed fields (`id`)
    * handles unique constraint violations as HTTP 400s (Bad Request)
    * modifies `is_valid()` to support temporarily ignoring unique constraints
    """

    def is_valid(
        self,
        raise_exception: bool = False,
        ignore_unique: bool = False,
    ) -> bool:
        """Adds a kwarg to temporarily remove all forms of unique validation from
        this serializer before it runs validation
        """
        # Inspired by https://stackoverflow.com/a/63782495/13789724

        # Skip extra work if it's unnecessary
        if not ignore_unique:
            return super().is_valid(raise_exception)

        # Save original validator list to reset with afterwards
        original_validators = copy(self.validators)

        def is_unique_validator(validator) -> bool:
            for unique_validator in [
                validators.UniqueValidator,
                validators.UniqueTogetherValidator,
                validators.BaseUniqueForValidator,
            ]:
                if isinstance(validator, unique_validator):
                    return True
            return False

        # Remove any unique validators from validation checks
        self.validators = [
            validator
            for validator in self.validators
            if not is_unique_validator(validator)
        ]

        # Run validation
        result = super().is_valid(raise_exception)

        # Reset validators
        self.validators = original_validators

        return result

    def save(self, **kwargs):
        """Extend Django's base `ModelSerializer` by returning unique constraint
        violations as HTTP 400s (Bad Request).
        """
        try:
            model: M = super().save(**kwargs)
            return model
        except IntegrityError as error:
            if "unique constraint" in str(error):
                raise serializers.ValidationError(
                    f"Graph already exists with properties {self.initial_data}"
                )
            raise error

    class Meta:
        model = M
        fields = ("id",)
        read_only_fields = ("id",)


class PopulationSerializer(_SimulationSerializer[Population]):
    """Serialization for simulation populations.

    No special behavior.
    """

    class Meta(_SimulationSerializer[Population].Meta):
        model = Population
        fields = (
            *_SimulationSerializer[Population].Meta.fields,
            "name",
            "initialism",
            "description",
        )


class ParametersSerializer(_SimulationSerializer[Parameters]):
    """Serialization for simulation parameters.

    No special behavior.
    """

    class Meta(_SimulationSerializer[Parameters].Meta):
        model = Parameters
        fields = (
            *_SimulationSerializer[Parameters].Meta.fields,
            "sample_size",
            "initial_infected_count",
            "cycles_per_day",
            "time_horizon",
            "exogenous_amount",
            "exogenous_frequency",
            "r0",
            "time_to_infection_mean",
            "time_to_infection_min",
            "time_to_recovery_mean",
            "time_to_recovery_min",
            "symptoms_probability",
            "death_probability",
            "test_specificity",
            "test_sensitivity",
            "test_cost",
            "test_results_delay",
            "test_rate",
        )


class InstanceSerializer(_SimulationSerializer[Instance]):
    """Serialization for viewing/updating simulation instances.

    Only `timestamp_end` may be updated (once an instance has
    finished simulating).
    """

    class Meta(_SimulationSerializer[Instance].Meta):
        model = Instance
        fields = (
            *_SimulationSerializer[Instance].Meta.fields,
            "parameters",
            "timestamp_start",
            "timestamp_end",
            "graph_id",
            "graph_type",
        )
        read_only_fields = (
            *_SimulationSerializer[Instance].Meta.fields,
            "parameters",
            "timestamp_start",
            "graph_id",
            "graph_type",
        )


class InstanceCreateSerializer(_SimulationSerializer[Instance]):
    """Serialization for listing/creating simulation instances.

    Only `parameters` may be specified; to edit `timestamp_end`
    after an instance has finished simulating, use
    `InstanceSerializer`.
    """

    class Meta(_SimulationSerializer[Instance].Meta):
        model = Instance
        fields = (
            *_SimulationSerializer[Instance].Meta.fields,
            "parameters",
            "timestamp_start",
            "timestamp_end",
            "graph_id",
            "graph_type",
        )
        read_only_fields = (
            *_SimulationSerializer[Instance].Meta.fields,
            "timestamp_start",
            "timestamp_end",
        )


class SampleSerializer(_SimulationSerializer[Sample]):
    """Serialization for simulation instance samples.

    No special behavior.
    """

    class Meta(_SimulationSerializer[Sample].Meta):
        model = Sample
        fields = (
            *_SimulationSerializer[Sample].Meta.fields,
            "instance",
            "timestamp_start",
            "timestamp_end",
        )
        read_only_fields = (
            *_SimulationSerializer[Sample].Meta.fields,
            "timestamp_start",
        )


class DataSerializer(_SimulationSerializer[Data]):
    """Serialization for simulation instance sample data.

    No special behavior.
    """

    class Meta(_SimulationSerializer[Data].Meta):
        model = Data
        fields = (
            *_SimulationSerializer[Data].Meta.fields,
            "sample",
            "timestamp",
            "cycle_index",
            "population",
            "population_size",
        )
        read_only_fields = (
            *_SimulationSerializer[Data].Meta.fields,
            "timestamp",
        )
