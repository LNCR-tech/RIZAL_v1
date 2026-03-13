import { useEffect } from "react";

interface UseRoleSidebarLayoutOptions {
  isExpanded: boolean;
  sidebarOpen: boolean;
}

export const useRoleSidebarLayout = ({
  isExpanded,
  sidebarOpen,
}: UseRoleSidebarLayoutOptions) => {
  useEffect(() => {
    const { body } = document;

    body.classList.add("has-role-sidebar");
    body.classList.toggle("sidebar-expanded", isExpanded);
    body.classList.toggle("sidebar-mobile-open", sidebarOpen);

    return () => {
      body.classList.remove(
        "has-role-sidebar",
        "sidebar-expanded",
        "sidebar-mobile-open"
      );
    };
  }, [isExpanded, sidebarOpen]);
};

export default useRoleSidebarLayout;
