import { formatINR } from "./utils";

describe("formatINR", () => {
  it("formats decimal strings from the API in Indian grouping", () => {
    expect(formatINR("123456.5")).toBe("₹1,23,456.50");
  });
});
