import { useMemo } from "react";
import { FaUserShield } from "react-icons/fa";

import NavbarAdmin from "../components/NavbarAdmin";
import NavbarSchoolIT from "../components/NavbarSchoolIT";
import PrivilegedFaceWorkspace from "../components/PrivilegedFaceWorkspace";
import type { FacialVerificationRole } from "../api/facialVerificationApi";
import "../css/FacialVerification.css";

interface FacialVerificationPageProps {
  role: FacialVerificationRole;
}

type StoredUserSnapshot = {
  email?: string;
  first_name?: string;
  last_name?: string;
  firstName?: string;
  lastName?: string;
};

const readStoredUser = (): StoredUserSnapshot | null => {
  try {
    const raw = localStorage.getItem("user");
    if (!raw) {
      return null;
    }
    return JSON.parse(raw) as StoredUserSnapshot;
  } catch {
    return null;
  }
};

const FacialVerification = ({ role }: FacialVerificationPageProps) => {
  const storedUser = useMemo(() => readStoredUser(), []);
  const roleLabel = role === "school_IT" ? "School IT" : "Admin";
  const NavbarComponent = role === "school_IT" ? NavbarSchoolIT : NavbarAdmin;
  const subjectId = storedUser?.email || role;
  const subjectLabel =
    storedUser?.first_name ||
    storedUser?.last_name ||
    storedUser?.firstName ||
    storedUser?.lastName
      ? `${storedUser?.first_name ?? storedUser?.firstName ?? ""} ${
          storedUser?.last_name ?? storedUser?.lastName ?? ""
        }`.trim()
      : subjectId;

  return (
    <div className="facial-verification-page">
      <NavbarComponent />
      <main className="facial-verification-shell">
        <section className="facial-verification-hero">
          <span className="facial-verification-badge">
            <FaUserShield />
            Backend Security
          </span>
          <h1>{roleLabel} Live Facial Verification</h1>
          <p>{subjectLabel}</p>
        </section>

        <PrivilegedFaceWorkspace
          role={role}
          subjectId={subjectId}
          subjectLabel={subjectLabel}
          variant="manage"
        />
      </main>
    </div>
  );
};

export default FacialVerification;
