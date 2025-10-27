# Use a base image with necessary tools
FROM ubuntu:20.04

# Set non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies and tools
RUN apt-get update && \
	apt-get install -y \
    build-essential \
	software-properties-common \ 
    gfortran \
    wget \
    curl \
    libx11-dev \
    libxext-dev \
    libxrender-dev \
    libxt-dev \
    vim \
	git \
	python3 \
	python3-pip \
    sudo \
    && rm -rf /var/lib/apt/lists/*

#### PGPLOT ####

# Set environment variables for PGPLOT
ENV PGPLOT_DIR=/usr/local/pgplot
ENV PGPLOT_FONT=/usr/local/pgplot/grfont.dat
ENV PGPLOT_DEV=/xw
ENV LD_LIBRARY_PATH=/usr/local/pgplot
#:${LD_LIBRARY_PATH:-}

# Create a non-root user
RUN groupadd -r snidgroup && \
    useradd -r -g snidgroup -m -d /home/sniduser -s /bin/bash sniduser
# Grant sniduser passwordless sudo privileges
RUN echo 'sniduser ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/sniduser && \
    chmod 0440 /etc/sudoers.d/sniduser

# Symlink gfortran to g77 
RUN ln -s /usr/bin/gfortran /usr/local/bin/g77

# Build PGPLOT
RUN mkdir /tmp/build \
    && cd /tmp/build \
    && wget ftp://ftp.astro.caltech.edu/pub/pgplot/pgplot5.2.tar.gz \
    && tar xvfz pgplot5.2.tar.gz \
    && cd pgplot \
    # Uncomment XWDRIV in drivers.list using a different delimiter
    && sed -i 's|^! XWDRIV 1 /XWINDOW|XWDRIV 1 /XWINDOW|' drivers.list \
    # Run makemake with appropriate system and compiler
    && ./makemake . linux g77_gcc \
    # Build PGPLOT and CPGPLOT
    && make \
    && make cpg \
    # Install PGPLOT to /usr/local/pgplot
    && cp -r /tmp/build/pgplot /usr/local/pgplot \
    # Clean up build directory
    && rm -rf /tmp/build

# Ensure /usr/local/pgplot is in the library path
RUN echo "/usr/local/pgplot" > /etc/ld.so.conf.d/pgplot.conf && ldconfig


### SNID ####


# Switch to the non-root user
USER sniduser

# Copy SNID source and templates tarball into the container
# Assuming you have snid-5.0.tar.gz and templates-2.0.tgz in your local directory
#RUN wget https://people.lam.fr/blondin.stephane/software/snid/templates-2.0.tgz && wget https://people.lam.fr/blondin.stephane/software/snid/snid-5.0.tar.gz
#COPY snid-5.0.tar.gz /home/sniduser/
#COPY templates-2.0.tgz /home/sniduser/

# Set working directory to sniduser's home
WORKDIR /home/sniduser

RUN wget https://people.lam.fr/blondin.stephane/software/snid/templates-2.0.tgz && wget https://people.lam.fr/blondin.stephane/software/snid/snid-5.0.tar.gz
# Extract SNID
RUN tar xvfz snid-5.0.tar.gz && rm snid-5.0.tar.gz

# Extract templates
RUN tar xvfz templates-2.0.tgz -C /home/sniduser/snid-5.0 && rm templates-2.0.tgz

# Copy the corrected Makefile into the SNID source directory with correct ownership
COPY --chown=sniduser:snidgroup Makefile /home/sniduser/snid-5.0/Makefile

# Install SNID
WORKDIR /home/sniduser/snid-5.0

# Edit SNID source files: snidmore.f and snid.inc
RUN sed -i "s|tempdir='INSTALL_DIR/snid-5.0/templates/'|tempdir='/home/sniduser/snid-5.0/templates-2.0/'|" source/snidmore.f && \
    sed -i "s|parameter (MAXPPT = .*|parameter (MAXPPT = 50000)|" source/snid.inc && \
    sed -i "s|parameter (MAXTEMP = .*|parameter (MAXTEMP = 10000)|" source/snid.inc

# Build SNID
RUN make clean && make

# Install SNID to /usr/local/bin (requires root)
USER root
RUN cp snid /usr/local/bin/

# Switch back to non-root user

# Set default command
#CMD ["/bin/bash"]

COPY run_snid.py /home/sniduser/snid-5.0/
RUN git clone https://github.com/cjduffy/pysnid.git && cd pysnid && pip install .
RUN pip install numpy pandas tables specutils typing astropy "fastapi[standard]"
COPY entrypoint.sh /entrypoint.sh 
RUN chmod +x /entrypoint.sh
USER root
ENTRYPOINT ["/entrypoint.sh"]
USER sniduser
CMD ["uvicorn", "run_snid:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

