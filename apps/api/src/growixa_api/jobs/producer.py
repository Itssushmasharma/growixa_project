import aio_pika

from growixa_api.config import get_settings
from growixa_api.jobs.schemas import JobEnvelope


async def publish_job(queue_name: str, envelope: JobEnvelope) -> None:
    connection = await aio_pika.connect_robust(get_settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue(queue_name, durable=True)
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=envelope.model_dump_json().encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=queue_name,
        )
