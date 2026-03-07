import { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  fetchSchoolSettings,
  getStoredBranding,
  normalizeLogoUrl,
  SchoolSettings,
} from "../api/schoolSettingsApi";

interface UserContextType {
  avatar: string | null;
  setAvatar: (userId: string, avatar: string) => void;
  branding: SchoolSettings | null;
  setBranding: (branding: SchoolSettings | null) => void;
  refreshBranding: () => Promise<void>;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const UserProvider = ({ children }: { children: React.ReactNode }) => {
  const [avatar, setAvatarState] = useState<string | null>(null);
  const [branding, setBrandingState] = useState<SchoolSettings | null>(() => {
    const stored = getStoredBranding();
    if (!stored) return null;
    return {
      ...stored,
      logo_url: normalizeLogoUrl(stored.logo_url),
    };
  });

  const setAvatar = (userId: string, newAvatar: string) => {
    localStorage.setItem(`userAvatar_${userId}`, newAvatar);
    setAvatarState(newAvatar);
  };

  const setBranding = (newBranding: SchoolSettings | null) => {
    if (!newBranding) {
      setBrandingState(null);
      return;
    }
    setBrandingState({
      ...newBranding,
      logo_url: normalizeLogoUrl(newBranding.logo_url),
    });
  };

  const refreshBranding = async () => {
    const token = localStorage.getItem("authToken") || localStorage.getItem("token");
    if (!token) return;

    try {
      const live = await fetchSchoolSettings();
      setBranding(live);
    } catch {
      // Branding fetch is best-effort so auth navigation is not blocked.
    }
  };

  useEffect(() => {
    refreshBranding();
  }, []);

  const value = useMemo(
    () => ({
      avatar,
      setAvatar,
      branding,
      setBranding,
      refreshBranding,
    }),
    [avatar, branding]
  );

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error("useUser must be used within a UserProvider");
  }
  return context;
};
