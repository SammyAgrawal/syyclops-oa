FROM eclipse-mosquitto:latest

# Copy configuration file
COPY config/mosquitto.conf /mosquitto/config/mosquitto.conf

# Create required directories
RUN mkdir -p /mosquitto/data /mosquitto/log

# Set permissions
RUN chown -R mosquitto:mosquitto /mosquitto

EXPOSE 1883 9001