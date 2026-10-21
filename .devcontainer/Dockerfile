FROM bioconductor/bioconductor_docker:RELEASE_3_23

ENV CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup
ENV PATH=/usr/local/cargo/bin:${PATH}

# The standard Rust feature adds ptrace and disables seccomp. Install only the
# toolchain so this diagnostic image needs neither permission.
RUN set -eux; \
    case "$(dpkg --print-architecture)" in \
      amd64) rust_arch=x86_64-unknown-linux-gnu ;; \
      arm64) rust_arch=aarch64-unknown-linux-gnu ;; \
      *) exit 1 ;; \
    esac; \
    cd /tmp; \
    curl -fsSLO "https://static.rust-lang.org/rustup/dist/${rust_arch}/rustup-init"; \
    curl -fsSLO "https://static.rust-lang.org/rustup/dist/${rust_arch}/rustup-init.sha256"; \
    sha256sum -c rustup-init.sha256; \
    chmod +x rustup-init; \
    ./rustup-init -y --no-modify-path --profile minimal --default-toolchain stable \
      --component rustfmt --component clippy --component rust-analyzer; \
    chown -R rstudio:rstudio "$CARGO_HOME" "$RUSTUP_HOME"; \
    rm rustup-init rustup-init.sha256
