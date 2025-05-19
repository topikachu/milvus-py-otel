import os
import pytest
from pymilvus import MilvusClient, DataType


from opentelemetry import trace
from opentelemetry.instrumentation.grpc import GrpcInstrumentorClient
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Set up environment variables
os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://localhost:4317'
os.environ['OTEL_SERVICE_NAME'] = 'milvus-client'

# Create a resource with the service name and application attributes
resource = Resource.create({
    "service.name": "milvus-client",
    "application": "milvus-otel-test"
})

# Set up the tracer provider with OTLP exporter
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(otlp_exporter)

trace.set_tracer_provider(
    TracerProvider(resource=resource)
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Instrument gRPC
grpc_client_instrumentor = GrpcInstrumentorClient()
grpc_client_instrumentor.instrument()

# Get a tracer
tracer = trace.get_tracer(__name__)

@pytest.fixture(scope="module")
def milvus_client():
    with tracer.start_as_current_span("milvus_client_setup"):
        client = MilvusClient(
            uri="http://localhost:19530",
        )
    yield client
    client.close()

def test_milvus_otel(milvus_client):
    with tracer.start_as_current_span("test_milvus_otel"):
        collection_name = "quick_setup"

        # Drop the collection if it exists
        if milvus_client.has_collection(collection_name):
            milvus_client.drop_collection(collection_name)

        # Create a collection
        milvus_client.create_collection(
            collection_name=collection_name,
            dimension=5
        )

        res = milvus_client.get_load_state(
            collection_name=collection_name
        )

        # Prepare the data
        data=[
            {"id": 0, "vector": [0.3580376395471989, -0.6023495712049978, 0.18414012509913835, -0.26286205330961354, 0.9029438446296592], "color": "pink_8682"},
            {"id": 1, "vector": [0.19886812562848388, 0.06023560599112088, 0.6976963061752597, 0.2614474506242501, 0.838729485096104], "color": "red_7025"},
            {"id": 2, "vector": [0.43742130801983836, -0.5597502546264526, 0.6457887650909682, 0.7894058910881185, 0.20785793220625592], "color": "orange_6781"},
            {"id": 3, "vector": [0.3172005263489739, 0.9719044792798428, -0.36981146090600725, -0.4860894583077995, 0.95791889146345], "color": "pink_9298"},
            {"id": 4, "vector": [0.4452349528804562, -0.8757026943054742, 0.8220779437047674, 0.46406290649483184, 0.30337481143159106], "color": "red_4794"},
            {"id": 5, "vector": [0.985825131989184, -0.8144651566660419, 0.6299267002202009, 0.1206906911183383, -0.1446277761879955], "color": "yellow_4222"},
            {"id": 6, "vector": [0.8371977790571115, -0.015764369584852833, -0.31062937026679327, -0.562666951622192, -0.8984947637863987], "color": "red_9392"},
            {"id": 7, "vector": [-0.33445148015177995, -0.2567135004164067, 0.8987539745369246, 0.9402995886420709, 0.5378064918413052], "color": "grey_8510"},
            {"id": 8, "vector": [0.39524717779832685, 0.4000257286739164, -0.5890507376891594, -0.8650502298996872, -0.6140360785406336], "color": "white_9381"},
            {"id": 9, "vector": [0.5718280481994695, 0.24070317428066512, -0.3737913482606834, -0.06726932177492717, -0.6980531615588608], "color": "purple_4976"}
        ]

        # Insert the data
        insert_result = milvus_client.insert(
            collection_name=collection_name,
            data=data
        )

        # Assert that 10 entities were inserted
        assert insert_result["insert_count"] == 10


        # Clean up
        milvus_client.drop_collection(collection_name)