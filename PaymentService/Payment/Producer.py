import sys
import os

from confluent_kafka import Producer

if __name__ == '__main__':
    topic = 'payment-statistic'
    
    conf = {
    'bootstrap.servers': 'localhost:9092',
    'session.timeout.ms': 6000,
    'default.topic.config': {'auto.offset.reset': 'smallest'}
    }
    
    p = Producer(**conf)
    
    def delivery_callback(err,msg):
        if err:
            sys.stderr.write('%% Message failed delivery: %s\n' % err)
        else:
            sys.stderr.write('%% Message delivered to %s [%d]\n' %
                            (msg.topic(), msg.partition()))
            
    line = "qdqdwqdqwdqwd"
    
    try:
        p.produce(topic, line.rstrip(), callback=delivery_callback)
    except BufferError as e:
        sys.stderr.write('%% Local producer queue is full (%d messages awaiting delivery): try again\n' %
                        len(p))
    p.poll(0)
    
    sys.stderr.write('%% Waiting for %d deliveries\n' % len(p))
    p.flush()
