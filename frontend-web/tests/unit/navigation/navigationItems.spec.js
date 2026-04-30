import { describe, expect, it } from "vitest";
import { getNavigationItemsForPath } from "@/components/navigation/navigationItems.js";

describe("navigation items", () => {
  it("returns preview dashboard navigation for exposed dashboard routes", () => {
    expect(
      getNavigationItemsForPath("/exposed/dashboard").map((item) => item.name),
    ).toEqual(["Home", "Schedule", "Analytics", "Profile"]);
  });

  it("returns preview workspace navigation for exposed workspace routes", () => {
    expect(
      getNavigationItemsForPath("/exposed/workspace").map((item) => item.name),
    ).toEqual(["Home", "Users", "Schedule", "Settings", "Profile"]);
  });
});
