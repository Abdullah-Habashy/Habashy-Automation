import ctypes
import sys
import time

# Define the MAGCOLOREFFECT structure
class MAGCOLOREFFECT(ctypes.Structure):
    _fields_ = [("transform", ctypes.c_float * 25)]

# Load the Magnification DLL
try:
    mag = ctypes.WinDLL('Magnification.dll')
except OSError:
    print("Error: Could not load Magnification.dll.")
    sys.exit(1)

# Initialize the Magnification API
mag.MagInitialize.restype = ctypes.c_bool
mag.MagUninitialize.restype = ctypes.c_bool
mag.MagSetFullscreenColorEffect.argtypes = [ctypes.POINTER(MAGCOLOREFFECT)]
mag.MagSetFullscreenColorEffect.restype = ctypes.c_bool

def get_grayscale_matrix():
    """Returns a simple Grayscale matrix."""
    matrix = MAGCOLOREFFECT()
    # Luminance weights: .2126, .7152, .0722
    weights = [0.2126, 0.7152, 0.0722]
    
    for i in range(3): # For each input channel (R, G, B)
        for j in range(3): # Map to each output channel (R, G, B)
            # transform[row * 5 + col]
            # Row i contributes to Output j
            matrix.transform[i * 5 + j] = weights[i]
            
    matrix.transform[18] = 1.0 # Alpha
    matrix.transform[24] = 1.0 # Translation W
    return matrix

def get_sepia_matrix():
    """
    Returns a 'Sepia/Amber' matrix for eye comfort.
    Converts to luminance, then tints warm (removes blue harshness).
    Resulting Tint: R=1.0, G=0.9, B=0.7 (Warm Paper)
    """
    matrix = MAGCOLOREFFECT()
    
    # Luminance weights
    lum_r, lum_g, lum_b = 0.2126, 0.7152, 0.0722
    
    # Tint factors (Warm Amber)
    tint_r, tint_g, tint_b = 1.0, 0.90, 0.65
    
    # Row 0: Input Red contribution
    matrix.transform[0] = lum_r * tint_r # Out Red
    matrix.transform[1] = lum_r * tint_g # Out Green
    matrix.transform[2] = lum_r * tint_b # Out Blue

    # Row 1: Input Green contribution
    matrix.transform[5] = lum_g * tint_r
    matrix.transform[6] = lum_g * tint_g
    matrix.transform[7] = lum_g * tint_b

    # Row 2: Input Blue contribution
    matrix.transform[10] = lum_b * tint_r
    matrix.transform[11] = lum_b * tint_g
    matrix.transform[12] = lum_b * tint_b

    matrix.transform[18] = 1.0 # Alpha
    matrix.transform[24] = 1.0 # Translation
    return matrix

def get_night_mode_matrix():
    """
    Deep Red/Orange matrix for maximum night vision protection.
    """
    matrix = MAGCOLOREFFECT()
    lum_r, lum_g, lum_b = 0.2126, 0.7152, 0.0722
    tint_r, tint_g, tint_b = 1.0, 0.5, 0.0 # mostly red
    
    matrix.transform[0] = lum_r * tint_r
    matrix.transform[1] = lum_r * tint_g
    matrix.transform[2] = lum_r * tint_b
    
    matrix.transform[5] = lum_g * tint_r
    matrix.transform[6] = lum_g * tint_g
    matrix.transform[7] = lum_g * tint_b
    
    matrix.transform[10] = lum_b * tint_r
    matrix.transform[11] = lum_b * tint_g
    matrix.transform[12] = lum_b * tint_b

    matrix.transform[18] = 1.0
    matrix.transform[24] = 1.0
    return matrix

def main():
    if not mag.MagInitialize():
        print("Error: Failed to initialize Magnification API.")
        return

    try:
        print("\n--- Eye Comfort Screen Tool ---")
        print("1. Standard Grayscale (Black & White)")
        print("2. Warm Sepia (Best for Reading/Eye Comfort)")
        print("3. Night Mode (Deep Orange/Red)")
        print("4. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        matrix = None
        mode_name = ""
        
        if choice == '1':
            matrix = get_grayscale_matrix()
            mode_name = "Grayscale"
        elif choice == '3':
            matrix = get_night_mode_matrix()
            mode_name = "Night Mode"
        else: # Default to 2
            matrix = get_sepia_matrix()
            mode_name = "Warm Sepia"

        print(f"\nApplying {mode_name}...")
        if not mag.MagSetFullscreenColorEffect(ctypes.byref(matrix)):
            print("Error: Could not set color effect. Try running as Administrator.")
            return

        print("\nFilter is ACTIVE.")
        print("Keep this window open to maintain the filter.")
        print("Press Ctrl+C to exit and return to normal colors.")
        
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
    finally:
        print("Restoring original screen colors...")
        mag.MagUninitialize()
        print("Done.")

if __name__ == "__main__":
    main()
