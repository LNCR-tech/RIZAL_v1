// src/api/recordsApi.ts
import axios from "axios";

import { buildApiUrl } from "./apiUrl";

// Fetch student records function
export const fetchStudentRecords = async () => {
  const response = await axios.get(buildApiUrl("/api/records"));
  return response.data;
};
