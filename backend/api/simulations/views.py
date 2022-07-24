"""
Endpoints to create, list, and retrieve individual objects relating to simulations.
"""

from django.db import transaction
from rest_framework import (
    mixins,
    viewsets,
    permissions,
    response,
    status,
)

from .models import Data, Instance, Parameters, Population, Sample
from .serializers import (
    DataSerializer,
    InstanceCreateSerializer,
    InstanceSerializer,
    ParametersSerializer,
    PopulationSerializer,
    SampleSerializer,
)
from .jobs import InstanceSamples


class _SimulationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """All simulation viewsets can list/retrieve their models.

    Permissions are currently unimplemented (`AllowAny`)."""

    permission_classes = (permissions.AllowAny,)


class PopulationViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    _SimulationViewSet,
):
    """Creates, updates, lists, and retrieves populations.

    To access graph raw data, see `CirculantGraphDataViewSet`.
    """

    queryset = Population.objects.all()
    serializer_class = PopulationSerializer


class ParametersViewSet(_SimulationViewSet):
    """Lists and retrieves parameters.

    New parameters row creation is done upon new simulation
    instances being generated.
    """

    queryset = Parameters.objects.all()
    serializer_class = ParametersSerializer


class InstanceViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    _SimulationViewSet,
):
    """Creates, updates, lists, and retrieves simulation instances.

    - create: checks if specified simulation parameters row already exists in
    the database, and creates a new parameters row if not.
    - update: only able to update the `timestamp_end` field.
    """

    # TODO: fix the schema for this to display `Parameters` fields for POST
    # see: https://github.com/tfranzel/drf-spectacular/

    queryset = Instance.objects.all()
    serializer_class = InstanceSerializer

    def get_serializer_class(self):
        # Use creation serializer class if this is a POST request (create a new instance)
        if self.action == "create":
            return InstanceCreateSerializer
        return super().get_serializer_class()

    # https://stackoverflow.com/a/54993327/13789724
    # Custom POST behavior
    def create(self, request, *args, **kwargs):
        """Checks if specified simulation parameters row already
        exists in the database, and creates a new parameters row
        if not.
        """

        data = request.data.copy()

        # Save simulation parameters from request data
        parameters = data.pop("parameters", {})

        # Ensure all parameter-parameters are found and valid,
        # and ignore unique constraints (since `get_or_create` below
        # will just grab the preexisting `Parameters` row)
        parameters_serializer = ParametersSerializer(data=parameters)
        parameters_serializer.is_valid(raise_exception=True, ignore_unique=True)

        # Required so that we do not create orphaned `parameters` rows
        with transaction.atomic():
            # Grab parameters ID if it already exists and store as `parameters_id` foreign key
            parameters_id, _ = Parameters.objects.get_or_create(**parameters)
            data["parameters"] = parameters_id.id

            # Ensure instance parameters are valid
            instance_serializer = InstanceCreateSerializer(data=data)
            instance_serializer.is_valid(raise_exception=True)

            # Save new simulation instance
            instance = instance_serializer.save()

            # Re-append parameter-parameters to instance serializer data
            instance_serializer.data["parameters"] = parameters
            headers = self.get_success_headers(instance_serializer.data)

            # Create simulation samples
            InstanceSamples(instance, InstanceSerializer(instance))

        # Success
        return response.Response(
            instance_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class SampleViewSet(_SimulationViewSet):
    """Lists and retrieves simulation instance samples.

    Samples are automatically generated by simulation instances.
    """

    queryset = Sample.objects.all()
    serializer_class = SampleSerializer


class DataViewSet(_SimulationViewSet):
    """Lists and retrieves simulation instance data.

    Data is automatically generated by simulation instance samples.
    """

    queryset = Data.objects.all()
    serializer_class = DataSerializer
