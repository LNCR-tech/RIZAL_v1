import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import BaseButton from "@/components/ui/BaseButton.vue";

describe("BaseButton", () => {
  it("renders slot content and respects loading state", () => {
    const wrapper = mount(BaseButton, {
      props: {
        loading: true,
      },
      slots: {
        default: "Log In",
      },
    });

    expect(wrapper.text()).toContain("Log In");
    expect(wrapper.attributes("disabled")).toBeDefined();
    expect(wrapper.find("svg").exists()).toBe(true);
  });

  it("applies the requested variant and size classes", () => {
    const wrapper = mount(BaseButton, {
      props: {
        variant: "secondary",
        size: "sm",
      },
      slots: {
        default: "Cancel",
      },
    });

    expect(wrapper.classes().join(" ")).toContain("border");
    expect(wrapper.classes().join(" ")).toContain("px-4");
  });
});
