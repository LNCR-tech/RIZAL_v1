import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useMemo } from "react";
import { isStudentFaceEnrollmentRequired } from "../api/studentFaceEnrollmentApi";

const ProtectedRoute = ({ allowedRoles }: { allowedRoles: string[] }) => {
  const storedUser = localStorage.getItem("user");
  const location = useLocation();

  // If no user is found, redirect to login
  if (!storedUser) {
    return <Navigate to="/" replace />;
  }

  // Parse user data safely
  const user = useMemo(() => {
    try {
      return JSON.parse(storedUser);
    } catch (error) {
      console.error("Error parsing user data:", error);
      return null;
    }
  }, [storedUser]);

  // If user data is invalid, redirect to login
  if (!user || !user.roles) {
    return <Navigate to="/" replace />;
  }

  const mustChangePassword = Boolean(user.mustChangePassword || user.must_change_password);
  if (mustChangePassword && location.pathname !== "/change-password") {
    return <Navigate to="/change-password" replace />;
  }

  const normalizeRole = (role: string) => role.trim().toLowerCase().replace(/_/g, "-");
  const userRoles = (user.roles as string[]).map(normalizeRole);
  const allowed = allowedRoles.map(normalizeRole);

  const requiresStudentFaceEnrollment =
    userRoles.includes("student") &&
    isStudentFaceEnrollmentRequired(typeof user.id === "number" ? user.id : null);

  if (
    requiresStudentFaceEnrollment &&
    location.pathname !== "/student_face_registration" &&
    location.pathname !== "/change-password"
  ) {
    return <Navigate to="/student_face_registration" replace />;
  }

  // Check if the user has at least one allowed role
  const hasAccess = allowed.some((role) => userRoles.includes(role));

  return hasAccess ? <Outlet /> : <Navigate to="/unauthorized" replace />;
};

export default ProtectedRoute;
