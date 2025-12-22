def calculate_region(x1, y1, x2, y2):
    left = x1
    top = y1
    width = x2 - x1
    height = y2 - y1
    return left, top, width, height


if __name__ == "__main__":
    print("=== Region Calculator ===")
    x1 = int(input("Enter x1 (left): "))
    y1 = int(input("Enter y1 (top): "))
    x2 = int(input("Enter x2 (right): "))
    y2 = int(input("Enter y2 (bottom): "))

    left, top, width, height = calculate_region(x1, y1, x2, y2)

    print("\nResult:")
    print(f"region = ({left}, {top}, {width}, {height})")
