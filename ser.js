import { useState, useEffect } from "react";

const ServiceSelector = ({ onSelect }) => {
  const [services, setServices] = useState([]);

  useEffect(() => {
    // Load services from a JSON config or API call
    fetch("/services.json")
      .then((response) => response.json())
      .then((data) => setServices(data.services))
      .catch((error) => console.error("Error loading services:", error));
  }, []);

  return (
    <div>
      <label>Select a Microservice:</label>
      <select onChange={(e) => onSelect(e.target.value)}>
        <option value="">-- Select --</option>
        {services.map((service) => (
          <option key={service.name} value={service.name}>
            {service.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default ServiceSelector;