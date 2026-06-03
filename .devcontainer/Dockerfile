# Use the official Ubuntu image as the base
FROM bioconductor/bioconductor_docker:RELEASE_3_23

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Declare that we expect a build argument named GITHUB_TOKEN
ARG GITHUB_TOKEN

# Convert the build argument into a permanent environment variable
# so the Dev Container feature scripts (like renv-cache) can see it
ENV GITHUB_TOKEN=${GITHUB_TOKEN}

# Copy the `.devcontainer/renv` folder to the container
COPY .devcontainer/renv /usr/local/share/renv-cache/renv

# Set appropriate permissions
RUN chmod -R 755 /usr/local/share/renv-cache/renv
