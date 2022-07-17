"""
Endpoints to create, list, and retrieve individual objects relating to simulations.
"""
from django.db import transaction
from rest_framework import mixins, viewsets, response, status
from rest_framework.permissions import AllowAny

from abseir import grapher

from .models import Data, Instance, Parameters, Population, Sample
from .serializers import (
    DataSerializer,
    InstanceSerializer,
    InstanceCreateSerializer,
    ParametersSerializer,
    PopulationSerializer,
    SampleSerializer,
)


class _SimulationViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """All simulation viewsets can list/retrieve their models.

    Permissions are currently unimplemented (`AllowAny`)."""

    permission_classes = (AllowAny,)


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
        if self.request.method == "POST":
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
        try:
            parameters = data.pop("parameters")
        except KeyError:
            return response.Response(status=status.HTTP_400_BAD_REQUEST)

        # Ensure all parameter-parameters are found and valid
        parameters_serializer = ParametersSerializer(data=parameters)
        parameters_serializer.is_valid(raise_exception=True)

        # Required so that we do not create orphaned `parameters` rows
        with transaction.atomic():
            # Grab parameters ID if it already exists and store as `parameters_id` foreign key
            parameters_id, _ = Parameters.objects.get_or_create(**parameters)
            data["parameters"] = parameters_id.id

            # Ensure instance parameters are valid
            instance_serializer: InstanceCreateSerializer = self.get_serializer(
                data=data
            )
            instance_serializer.is_valid(raise_exception=True)

            # Save new simulation instance
            instance_serializer.save()

            # Re-append parameter-parameters to instance serializer data
            instance_serializer.data["parameters"] = parameters
            headers = self.get_success_headers(instance_serializer.data)

            # Success
            return response.Response(
                instance_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
