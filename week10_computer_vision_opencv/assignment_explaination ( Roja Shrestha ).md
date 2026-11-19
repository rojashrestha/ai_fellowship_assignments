# Computer Vision Assignment - Plain English Explanation

This document explains all four parts of the computer vision assignment in simple, clear English.

---

## Part A - Color Space and Fruit Segmentation

### A1: BGR vs RGB Display
- OpenCV loads images in BGR order (Blue, Green, Red).
- Matplotlib displays images in RGB order (Red, Green, Blue).
- If we do not convert channels, colors look wrong. For example, a red apple will look blue because the red and blue channels are swapped.
- We use cv2.cvtColor(image, cv2.COLOR_BGR2RGB) to fix the color order.

### A2: HSV Channel Visualization
- HSV stands for Hue (color type), Saturation (color intensity), and Value (brightness).
- Hue is useful because it represents the actual color and does not change much with lighting variations.
- The Saturation channel is the best channel to separate the fruit from the white background.
- This is because the white background has very low saturation (close to 0), while the fruit has very high saturation (vivid colors).

### A3: Red Apple HSV Masking
- Red is a unique color because it wraps around the Hue axis. It is located at both the very beginning (0 to 10) and the very end (170 to 180) of the Hue range in OpenCV.
- To detect a red fruit, we create two separate masks using cv2.inRange() and then merge them using cv2.bitwise_or().
- We extract the fruit by applying cv2.bitwise_and() between the original image and the combined mask.

### A4: Color Table
Here are the HSV working ranges used for each fruit:
- Red Apple: Hue range 0 to 10 AND 170 to 180, Saturation 70 to 255, Value 50 to 255.
- Green Apple: Hue range 30 to 85, Saturation 40 to 255, Value 40 to 255.
- Banana: Hue range 20 to 35, Saturation 80 to 255, Value 80 to 255.
- Lime: Hue range 30 to 80, Saturation 50 to 255, Value 50 to 255.

### A5: Brightness and Contrast
- Dark images make color masking fail. We can fix this by increasing brightness and contrast.
- The formula is: adjusted = alpha * pixel + beta, where alpha controls contrast and beta controls brightness.
- Using NumPy math or OpenCV's cv2.convertScaleAbs() gives the exact same result.
- Brighter images make the HSV mask much more reliable.

### A6: Reflection - HSV vs RGB
- HSV works better than RGB because color (Hue) and brightness (Value) are separated. If warehouse lighting changes, only Value changes, while Hue stays constant.
- HSV fails when fruits are extremely dark (like dark grapes or blueberries) because when Value is close to zero, Hue becomes noisy and loses its meaning.

---

## Part B - Histograms and Filtering

### B1: Strawberry Histogram
- A histogram counts how many pixels exist at each brightness level (from 0 to 255).
- If the histogram is spread out across the chart, the image has good contrast. If it is bunched up, contrast is poor.
- The strawberry image has good contrast with peaks showing the fruit and the background separately.

### B2: Histogram Equalization and CLAHE
- Global Histogram Equalization stretches pixel brightness to cover the full range. It can over-amplify contrast and distort images.
- CLAHE (Contrast Limited Adaptive Histogram Equalization) divides the image into small tiles and equalizes them locally.
- CLAHE with clipLimit=2.0 gives the best, most natural enhancement without amplifying noise.

### B3: Noise and Denoising Filters
- Camera sensors create grainy noise. We test three filters to remove it:
- Gaussian Blur: Smooths noise but also blurs the object edges.
- Median Filter: Takes the middle pixel value. Good for sharp noise.
- Bilateral Filter: Smoothes flat areas but keeps edges sharp by checking pixel distance and color similarity. It is the best filter for keeping fruit edges sharp.

### B4: Manual Convolution
- Convolution slides a small grid (kernel) over the image, multiplying and summing values at each step.
- The Sobel X kernel detects vertical edges by finding changes in horizontal brightness.
- The custom Python convolution and OpenCV's cv2.filter2D() produce matching results.

---

## Part C - Morphology and Mask Cleanup

### C1: Erosion on Banana Mask
- Erosion shrinks the white shapes in a binary mask by checking if the kernel is fully inside the shape.
- Sano noise dots disappear, but the main object edges also shrink slightly.

### C2: Opening and Closing
- Opening is erosion followed by dilation. It removes small background noise.
- Closing is dilation followed by erosion. It fills small holes and gaps inside the object.
- Using them together cleans up rough color masks.

### C3: Morphological Gradient
- The gradient is computed by subtracting the eroded mask from the dilated mask.
- This isolates the thin boundary outline of the fruit, which can be drawn as a green overlay on the original image.

### C4: Morphology on BGR Image
- Applying erosion or dilation directly to a BGR color image (instead of a binary mask) distorts colors and makes them bleed.
- Erosion darkens the overall image. Dilation brightens it. It is not useful for object segmentation.

### C5: j.png Demo
- Erosion, dilation, opening, closing, top hat, and black hat are tested on a letter J shape.
- The Top Hat operation (original minus opening) is the best way to isolate thin strokes.

---

## Part D - Edge and Feature Detection

### D1: Canny Edge Detection
- Canny is a multi-step edge detector: blur, gradient calculation, non-maximum suppression (thinning), and double thresholding with hysteresis.
- Lower thresholds (like 30, 100) capture too many small textures and noise.
- Higher thresholds (like 100, 200) capture only the clean, strong outer boundary of the fruit.

### D2: Canny from Scratch
- Implementing the 5 steps manually helps us understand how edges are detected.
- The custom implementation matches OpenCV's cv2.Canny() output, confirming that the mathematical logic is identical.

### D3: Harris Corner Detection
- Harris corner detection finds corners by analyzing intensity changes in all directions.
- Adjusting the response threshold from 0.01 to 0.1 makes the detector more selective, marking only the strongest corner points.

### D4: Hough Circle Transform
- Hough Circle Transform uses a voting system to find circles of a given radius range.
- We tune param2 (the accumulator threshold) to control sensitivity.
- It only detects round fruits (like apples and oranges) and ignores non-round shapes (like bananas).

### D5: Full Pipeline
- The complete pipeline runs as follows: Load BGR -> Convert to HSV -> Apply color mask -> Clean with morphology (opening/closing) -> Extract Canny edges -> Find contours -> Draw bounding box -> Save image.
- This automatically detects, segments, and outlines individual fruits.
