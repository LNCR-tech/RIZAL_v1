import React, { useEffect } from 'react';
import { AuthProvider, useAuth } from '../../context/AuthContext';
import { normalizeRole } from '../../config/roles';
import { useAuthorizedEmails, canAccessTechnicalDocs } from '../../config/emailAuth';

function BodyClassManager() {
  const { user, role } = useAuth();
  const authorizedEmails = useAuthorizedEmails();

  useEffect(() => {
    const roleClassPrefix = 'role-';
    const existingRoleClasses = Array.from(document.body.classList).filter((className) =>
      className.startsWith(roleClassPrefix)
    );

    existingRoleClasses.forEach((className) => document.body.classList.remove(className));

    if (user) {
      document.body.classList.add('user-authenticated');
      document.body.classList.remove('user-anonymous');
    } else {
      document.body.classList.remove('user-authenticated');
      document.body.classList.add('user-anonymous');
    }

    const normalizedRole = normalizeRole(role);
    if (normalizedRole) {
      document.body.classList.add(`${roleClassPrefix}${normalizedRole}`);
    }

    document.body.classList.toggle(
      'can-access-technical-docs',
      canAccessTechnicalDocs(user, role, authorizedEmails)
    );
  }, [user, role, authorizedEmails]);

  return null;
}

export default function Root({ children }) {
  return (
    <AuthProvider>
      <BodyClassManager />
      {children}
    </AuthProvider>
  );
}
