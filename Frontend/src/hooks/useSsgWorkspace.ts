import { useGovernanceWorkspace } from "./useGovernanceWorkspace";

export const useSsgWorkspace = () => {
  const workspace = useGovernanceWorkspace("SSG");
  return {
    ...workspace,
    ssgAccessUnit: workspace.accessUnit,
    ssgUnit: workspace.governanceUnit,
  };
};

export default useSsgWorkspace;
