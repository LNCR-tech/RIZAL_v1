import React from "react";
import { ManualAttendance } from "./ManualAttendance";

interface AttendanceProps {
  role: string;
}

export const Attendance: React.FC<AttendanceProps> = ({ role }) => {
  return <ManualAttendance role={role} />;
};

export default Attendance;
