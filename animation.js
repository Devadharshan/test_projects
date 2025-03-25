import { useEffect, useRef } from "react";
import * as THREE from "three";

const ThreeJSAnimation = ({ trigger }) => {
  const mountRef = useRef(null);

  useEffect(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ alpha: true });
    
    renderer.setSize(300, 300);
    mountRef.current.appendChild(renderer.domElement);

    const geometry = new THREE.SphereGeometry(1, 32, 32);
    const material = new THREE.MeshBasicMaterial({ color: 0x0077ff, wireframe: true });
    const sphere = new THREE.Mesh(geometry, material);
    
    scene.add(sphere);
    camera.position.z = 3;

    const animate = () => {
      requestAnimationFrame(animate);
      sphere.rotation.y += 0.02;
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      mountRef.current.removeChild(renderer.domElement);
    };
  }, [trigger]);

  return <div ref={mountRef} />;
};

export default ThreeJSAnimation;