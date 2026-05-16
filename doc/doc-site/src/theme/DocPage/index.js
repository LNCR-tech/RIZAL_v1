import React from 'react';
import DocPage from '@theme-original/DocPage';
import { useLocation } from '@docusaurus/router';
import { useAuth } from '../../context/AuthContext';
import { useAuthorizedEmails, canAccessTechnicalDocs } from '../../config/emailAuth';
import AccessDenied from '../../components/AccessDenied/AccessDenied';
import EmailLogin from '../../components/EmailLogin/EmailLogin';

export default function DocPageWrapper(props) {
  const location = useLocation();
  const { user, role, loading } = useAuth();
  const authorizedEmails = useAuthorizedEmails();

  if (loading) {
    return <DocPage {...props} />;
  }

  const isTechnicalDoc = location.pathname.startsWith('/technical');

  if (!user) {
    return <EmailLogin />;
  }

  if (isTechnicalDoc && !canAccessTechnicalDocs(user, role, authorizedEmails)) {
    return <AccessDenied />;
  }

  return <DocPage {...props} />;
}
