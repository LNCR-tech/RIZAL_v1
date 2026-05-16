import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import { hasAdminPrivileges } from './roles';

const splitEmails = (rawValue) =>
  String(rawValue || '')
    .split(',')
    .map((email) => email.trim().toLowerCase())
    .filter(Boolean);

export const useAuthorizedEmails = () => {
  const { siteConfig } = useDocusaurusContext();
  return splitEmails(siteConfig.customFields?.authorizedEmails);
};

export const isAuthorizedEmail = (email, authorizedList) => {
  if (!email || !Array.isArray(authorizedList)) return false;
  return authorizedList.includes(String(email).trim().toLowerCase());
};

export const getUserEmail = (user) => {
  if (!user) return '';
  if (user.email) return user.email;
  if (user.username && String(user.username).includes('@')) return user.username;
  return '';
};

export const canAccessTechnicalDocs = (user, role, authorizedList) => {
  if (hasAdminPrivileges(role)) return true;
  return isAuthorizedEmail(getUserEmail(user), authorizedList);
};
