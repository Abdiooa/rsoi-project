import sys
import os
import random
import string
from confluent_kafka import Consumer, KafkaException, KafkaError

if __name__ == "__main__":
    topics = ['payment-statistic']
    conf = {
        'bootstrap.servers': '157.230.71.224:9092,146.190.188.54:9092', 
        'session.timeout.ms': 6000,
        'group.id': 'dmqj25d74voir-consumer',
        'default.topic.config': {'auto.offset.reset': 'smallest'}
    }

    c = Consumer(**conf)
    c.subscribe(topics)
    
    try:
        while True:
            msg = c.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                    (msg.topic(), msg.partition(), msg.offset()))
                elif msg.error():
                    raise KafkaException(msg.error())
            else:
                sys.stderr.write('%% %s [%d] at offset %d with key %s:\n' %
                                (msg.topic(), msg.partition(), msg.offset(),
                                str(msg.key())))
                print(msg.value())
    except KeyboardInterrupt:
        sys.stderr.write('%% Aborted by user\n')
        
    c.close()
    
