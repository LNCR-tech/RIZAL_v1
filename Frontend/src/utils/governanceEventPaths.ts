import { GovernanceContext } from "../api/eventsApi";

export const getGovernanceEventsPath = (governanceContext: GovernanceContext) => {
  if (governanceContext === "SSG") {
    return "/ssg_events";
  }
  if (governanceContext === "SG") {
    return "/sg_events";
  }
  return "/org_events";
};

export const getGovernanceEventDetailsPath = (
  governanceContext: GovernanceContext,
  eventId: number
) => `${getGovernanceEventsPath(governanceContext)}/${eventId}`;
