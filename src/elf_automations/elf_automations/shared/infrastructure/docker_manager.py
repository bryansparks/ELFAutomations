"""
Docker registry and image management automation

Handles:
- Local registry setup
- Image building and tagging
- Image transfer between environments
- Registry cleanup and maintenance
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import docker

logger = logging.getLogger(__name__)


@dataclass
class DockerImage:
    """Docker image information"""

    name: str
    tag: str
    registry: Optional[str] = None

    @property
    def full_name(self) -> str:
        """Get full image name with registry"""
        if self.registry:
            return f"{self.registry}/{self.name}:{self.tag}"
        return f"{self.name}:{self.tag}"


class DockerManager:
    """Manages Docker operations and local registry"""

    def __init__(
        self,
        registry_host: str = "localhost:5000",
        remote_host: Optional[str] = None,
        remote_user: Optional[str] = None,
    ):
        """
        Initialize Docker manager

        Args:
            registry_host: Local registry host:port
            remote_host: Remote host for transfers (e.g., "192.168.6.5")
            remote_user: SSH user for remote host
        """
        self.registry_host = registry_host
        self.remote_host = remote_host
        self.remote_user = remote_user

        try:
            self.client = docker.from_env()
            logger.info("Connected to Docker daemon")
        except Exception as e:
            logger.error(f"Failed to connect to Docker: {e}")
            self.client = None

    def setup_local_registry(self) -> bool:
        """Setup local Docker registry"""
        if not self.client:
            logger.error("Docker client not available")
            return False

        try:
            # Check if registry already exists
            try:
                container = self.client.containers.get("registry")
                if container.status == "running":
                    logger.info("Registry already running")
                    return True
                else:
                    container.start()
                    logger.info("Started existing registry")
                    return True
            except docker.errors.NotFound:
                pass

            # Create new registry
            logger.info("Creating local Docker registry...")
            container = self.client.containers.run(
                "registry:2",
                name="registry",
                ports={"5000/tcp": 5000},
                restart_policy={"Name": "always"},
                detach=True,
                volumes={
                    "/var/lib/registry": {"bind": "/var/lib/registry", "mode": "rw"}
                },
            )

            logger.info(f"Registry created: {container.id[:12]}")

            # Test registry
            test_result = self._test_registry()
            if test_result:
                logger.info("Registry test successful")
            else:
                logger.error("Registry test failed")

            return test_result

        except Exception as e:
            logger.error(f"Failed to setup registry: {e}")
            return False

    def _test_registry(self) -> bool:
        """Test if registry is accessible"""
        try:
            import requests

            response = requests.get(f"http://{self.registry_host}/v2/")
            return response.status_code == 200
        except:
            return False

    def build_image(
        self,
        path: str,
        image_name: str,
        tag: str = "latest",
        push_to_registry: bool = True,
    ) -> Optional[DockerImage]:
        """
        Build Docker image

        Args:
            path: Path to directory with Dockerfile
            image_name: Image name
            tag: Image tag
            push_to_registry: Whether to push to local registry

        Returns:
            DockerImage object or None on failure
        """
        if not self.client:
            logger.error("Docker client not available")
            return None

        try:
            # Build image
            logger.info(f"Building image {image_name}:{tag} from {path}")

            image, build_logs = self.client.images.build(
                path=path,
                tag=f"{image_name}:{tag}",
                rm=True,  # Remove intermediate containers
                pull=True,  # Always pull base images
            )

            # Log build output
            for log in build_logs:
                if "stream" in log:
                    logger.debug(log["stream"].strip())

            docker_image = DockerImage(name=image_name, tag=tag)

            # Push to registry if requested
            if push_to_registry:
                registry_image = self.push_to_registry(docker_image)
                if registry_image:
                    return registry_image

            return docker_image

        except Exception as e:
            logger.error(f"Failed to build image: {e}")
            return None

    def push_to_registry(self, image: DockerImage) -> Optional[DockerImage]:
        """Push image to local registry"""
        if not self.client:
            return None

        try:
            # Tag for registry
            registry_tag = f"{self.registry_host}/{image.name}:{image.tag}"

            logger.info(f"Tagging image as {registry_tag}")
            self.client.images.get(image.full_name).tag(registry_tag)

            # Push to registry
            logger.info(f"Pushing to registry...")
            push_logs = self.client.images.push(registry_tag, stream=True, decode=True)

            for log in push_logs:
                if "status" in log:
                    logger.debug(f"{log.get('status')} {log.get('progress', '')}")

            return DockerImage(
                name=image.name, tag=image.tag, registry=self.registry_host
            )

        except Exception as e:
            logger.error(f"Failed to push to registry: {e}")
            return None

    def pull_from_registry(self, image: DockerImage) -> bool:
        """Pull image from registry"""
        if not self.client:
            return False

        try:
            logger.info(f"Pulling {image.full_name}")
            self.client.images.pull(image.full_name)
            return True
        except Exception as e:
            logger.error(f"Failed to pull image: {e}")
            return False

    def list_images(self, filter_name: Optional[str] = None) -> List[DockerImage]:
        """List Docker images"""
        if not self.client:
            return []

        images = []
        for img in self.client.images.list():
            for tag in img.tags:
                if filter_name and filter_name not in tag:
                    continue

                # Parse tag
                if "/" in tag:
                    registry, rest = tag.split("/", 1)
                    name, version = (
                        rest.split(":", 1) if ":" in rest else (rest, "latest")
                    )
                    images.append(
                        DockerImage(name=name, tag=version, registry=registry)
                    )
                else:
                    name, version = tag.split(":", 1) if ":" in tag else (tag, "latest")
                    images.append(DockerImage(name=name, tag=version))

        return images

    def cleanup_old_images(self, keep_last: int = 5):
        """Clean up old images, keeping the most recent ones"""
        if not self.client:
            return

        logger.info(f"Cleaning up old images (keeping last {keep_last})")

        # Group images by name
        image_groups = {}
        for img in self.client.images.list():
            for tag in img.tags:
                base_name = tag.split(":")[0]
                if base_name not in image_groups:
                    image_groups[base_name] = []
                image_groups[base_name].append((img, tag))

        # Clean up old versions
        for base_name, images in image_groups.items():
            if len(images) > keep_last:
                # Sort by creation date
                images.sort(key=lambda x: x[0].attrs["Created"], reverse=True)

                # Remove old ones
                for img, tag in images[keep_last:]:
                    try:
                        logger.info(f"Removing old image: {tag}")
                        self.client.images.remove(img.id, force=True)
                    except Exception as e:
                        logger.warning(f"Failed to remove {tag}: {e}")


class ImageTransfer:
    """Handles Docker image transfers between machines"""

    def __init__(self, docker_manager: DockerManager):
        """
        Initialize image transfer

        Args:
            docker_manager: DockerManager instance with remote_host configured
        """
        self.docker = docker_manager

    def transfer_image(self, image: DockerImage, compress: bool = True) -> bool:
        """
        Transfer Docker image to remote host

        Args:
            image: Docker image to transfer
            compress: Whether to compress the transfer

        Returns:
            True if successful
        """
        if not self.docker.remote_host or not self.docker.remote_user:
            logger.error("Remote host not configured")
            return False

        try:
            # Save image to tar
            logger.info(f"Saving image {image.full_name}")
            tar_path = f"/tmp/{image.name}-{image.tag}.tar"

            if compress:
                tar_path += ".gz"
                save_cmd = f"docker save {image.full_name} | gzip > {tar_path}"
            else:
                save_cmd = f"docker save {image.full_name} > {tar_path}"

            subprocess.run(save_cmd, shell=True, check=True)

            # Transfer to remote
            logger.info(f"Transferring to {self.docker.remote_host}")
            scp_cmd = [
                "scp",
                tar_path,
                f"{self.docker.remote_user}@{self.docker.remote_host}:{tar_path}",
            ]
            subprocess.run(scp_cmd, check=True)

            # Load on remote
            logger.info("Loading image on remote host")

            if compress:
                load_cmd = f"gunzip -c {tar_path} | docker load"
            else:
                load_cmd = f"docker load < {tar_path}"

            ssh_cmd = [
                "ssh",
                f"{self.docker.remote_user}@{self.docker.remote_host}",
                load_cmd,
            ]
            subprocess.run(ssh_cmd, check=True)

            # Cleanup
            os.remove(tar_path)
            ssh_cleanup = [
                "ssh",
                f"{self.docker.remote_user}@{self.docker.remote_host}",
                f"rm {tar_path}",
            ]
            subprocess.run(ssh_cleanup, check=True)

            logger.info(f"Successfully transferred {image.full_name}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            return False

    def sync_all_images(
        self, name_filter: Optional[str] = "elf-automations"
    ) -> Tuple[int, int]:
        """
        Sync all matching images to remote host

        Args:
            name_filter: Filter images by name

        Returns:
            Tuple of (successful_transfers, failed_transfers)
        """
        images = self.docker.list_images(name_filter)
        logger.info(f"Found {len(images)} images to sync")

        success = 0
        failed = 0

        for image in images:
            if self.transfer_image(image):
                success += 1
            else:
                failed += 1

        logger.info(f"Sync complete: {success} successful, {failed} failed")
        return success, failed

    def setup_remote_registry_access(self) -> bool:
        """Configure remote host to access local registry"""
        if not self.docker.remote_host or not self.docker.remote_user:
            return False

        try:
            # Get local machine IP
            import socket

            local_ip = socket.gethostbyname(socket.gethostname())

            # Add insecure registry to remote Docker config
            logger.info(f"Configuring remote Docker to access {local_ip}:5000")

            config_cmd = f"""
            sudo mkdir -p /etc/docker
            echo '{{
              "insecure-registries": ["{local_ip}:5000"]
            }}' | sudo tee /etc/docker/daemon.json
            sudo systemctl restart docker
            """

            ssh_cmd = [
                "ssh",
                f"{self.docker.remote_user}@{self.docker.remote_host}",
                config_cmd,
            ]

            subprocess.run(ssh_cmd, check=True)
            logger.info("Remote registry access configured")
            return True

        except Exception as e:
            logger.error(f"Failed to setup remote registry access: {e}")
            return False
