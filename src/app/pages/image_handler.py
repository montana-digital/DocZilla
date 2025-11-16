"""
Image File Handler Page

Upload, preview, convert, compress, crop, and combine images.
"""

import streamlit as st
from pathlib import Path
from typing import List, Tuple

# Imports using proper package structure
from src.app.components.layout import render_page_header, render_sidebar, render_quick_start
from src.app.utils.config import get_config
from src.app.services.file_io import generate_timestamped_filename

# Optional dependencies
try:
    from PIL import Image, ImageOps
except Exception:
    Image = None

try:
    from streamlit_cropper import st_cropper  # type: ignore
except Exception:
    st_cropper = None

# Streamlit multipage: Don't call st.set_page_config() here

render_sidebar()
config = get_config()

render_page_header(
    title="🖼️ Image File Handler",
    subtitle="Convert, compress, crop, and combine images"
)

render_quick_start([
    "Upload images or load from Input directory",
    "Preview and convert formats (PNG/JPG/TIFF/WEBP)",
    "Compress by quality, crop (if cropper available)",
    "Combine up to 9 images into a grid and save at 300 DPI"
])

if Image is None:
    st.error("Pillow (PIL) is required. Install with: pip install Pillow")
    st.stop()

# Session state
if "images" not in st.session_state:
    st.session_state.images = {}  # name -> {path, image}

# Tabs
utab, ctab, crop_tab, grid_tab = st.tabs([
    "📤 Upload & Preview", "🔄 Convert/Compress", "✂️ Crop", "🧩 Grid Combine"
])

# -----------------------------
# Upload & Preview
# -----------------------------
with utab:
    cols = st.columns([3, 1])
    with cols[0]:
        uploaded = st.file_uploader(
            "Drag and drop images",
            type=["png", "jpg", "jpeg", "tiff", "webp", "gif", "bmp"],
            accept_multiple_files=True
        )
    with cols[1]:
        if st.button("📂 Load from Input Dir"):
            inp = Path(config.get("directories.input", "./input"))
            if inp.exists():
                cnt = 0
                for p in sorted(inp.iterdir()):
                    if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tiff", ".webp", ".gif", ".bmp"}:
                        try:
                            img = Image.open(p).convert("RGB")
                            st.session_state.images[p.name] = {"path": p, "image": img}
                            cnt += 1
                        except Exception:
                            pass
                st.success(f"Loaded {cnt} image(s) from Input")
            else:
                st.info("Input directory not found")

    if uploaded:
        for uf in uploaded:
            tmp = Path("temp") / uf.name
            tmp.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, "wb") as f:
                f.write(uf.getbuffer())
            try:
                img = Image.open(tmp).convert("RGB")
                st.session_state.images[uf.name] = {"path": tmp, "image": img}
            except Exception as e:
                st.warning(f"Failed to load {uf.name}: {e}")
        st.success(f"Loaded {len(uploaded)} image(s)")

    if st.session_state.images:
        names = list(st.session_state.images.keys())
        sel = st.selectbox("Preview image", names)
        if sel:
            st.image(st.session_state.images[sel]["image"], caption=sel, use_column_width=True)
    else:
        st.info("Upload or load images to begin")

# -----------------------------
# Convert / Compress
# -----------------------------
with ctab:
    if not st.session_state.images:
        st.info("Upload images first")
    else:
        names = list(st.session_state.images.keys())
        multi = st.multiselect("Select images", names, default=names[: min(5, len(names))])
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Convert**")
            target = st.selectbox("Format", ["png", "jpg", "webp", "tiff"], key="img_conv_fmt")
            if st.button("Convert Selected", key="img_convert_btn") and multi:
                out_dir = Path(config.get("directories.output", "./output"))
                out_dir.mkdir(parents=True, exist_ok=True)
                ok = 0
                for n in multi:
                    img = st.session_state.images[n]["image"]
                    base = Path(n).stem
                    fname = generate_timestamped_filename(base, target)
                    dest = out_dir / fname
                    try:
                        fmt = target.upper()
                        if fmt in {"PNG", "TIFF", "JPEG"}:
                            img.save(dest, format=fmt, dpi=(300, 300))
                        else:
                            img.save(dest, format=fmt)
                        ok += 1
                    except Exception as e:
                        st.warning(f"Failed to convert {n}: {e}")
                st.success(f"Converted {ok}/{len(multi)}")
        with col2:
            st.markdown("**Compress**")
            quality = st.slider("Quality (JPG/WEBP)", 10, 100, 80)
            if st.button("Compress Selected", key="img_compress_btn") and multi:
                out_dir = Path(config.get("directories.output", "./output"))
                out_dir.mkdir(parents=True, exist_ok=True)
                ok = 0
                for n in multi:
                    img = st.session_state.images[n]["image"]
                    base = Path(n).stem
                    fname = generate_timestamped_filename(base + "_compressed", Path(n).suffix.lstrip('.'))
                    dest = out_dir / fname
                    try:
                        fmt = Path(fname).suffix.lstrip('.').upper()
                        if fmt in {"JPG", "JPEG"}:
                            img.save(dest, format="JPEG", quality=quality, optimize=True, dpi=(300, 300))
                        elif fmt == "WEBP":
                            img.save(dest, format="WEBP", quality=quality, method=6)
                        else:
                            # For PNG/TIFF, fallback to save (PNG compression not quality based here)
                            img.save(dest, format=fmt, dpi=(300, 300))
                        ok += 1
                    except Exception as e:
                        st.warning(f"Failed to compress {n}: {e}")
                st.success(f"Compressed {ok}/{len(multi)}")

# -----------------------------
# Crop
# -----------------------------
with crop_tab:
    if not st.session_state.images:
        st.info("Upload images first")
    elif st_cropper is None:
        st.info("Install streamlit-cropper to enable cropping: pip install streamlit-cropper")
    else:
        names = list(st.session_state.images.keys())
        name = st.selectbox("Select image to crop", names)
        img = st.session_state.images[name]["image"]
        st.markdown("Adjust crop rectangle and click Save")
        cropped = st_cropper(img, aspect_ratio=None, box_color='#27ae60', return_type='image')
        if st.button("Save Crop", key="save_crop"):
            out_dir = Path(config.get("directories.output", "./output"))
            out_dir.mkdir(parents=True, exist_ok=True)
            base = Path(name).stem
            dest = out_dir / generate_timestamped_filename(base + "_crop", "png")
            try:
                cropped.save(dest, format="PNG")
                st.success(f"Saved crop: {dest.name}")
            except Exception as e:
                st.error(f"Crop save failed: {e}")

# -----------------------------
# Grid Combine
# -----------------------------
with grid_tab:
    if not st.session_state.images:
        st.info("Upload images first")
    else:
        st.markdown("Combine up to 9 images into a grid (300 DPI)")
        names = list(st.session_state.images.keys())
        selected = st.multiselect("Select up to 9 images", names, max_selections=9)
        cols = st.slider("Grid columns", 1, 3, 3)
        pad = st.number_input("Padding (px)", min_value=0, max_value=50, value=8)
        
        # Labeling options
        st.markdown("**Labeling**")
        label_mode = st.radio(
            "Label style",
            ["None", "Filename", "Custom (1, 2, 3...)", "Autonum"],
            index=1,
            key="label_mode"
        )
        custom_labels = []
        if label_mode == "Custom (1, 2, 3...)":
            for i, name in enumerate(selected, 1):
                label = st.text_input(f"Label for {name}", value=str(i), key=f"label_{i}")
                custom_labels.append(label)
        
        if st.button("Build Grid", key="build_grid") and selected:
            imgs: List[Image.Image] = [st.session_state.images[n]["image"] for n in selected]
            # Compute grid
            rows = (len(imgs) + cols - 1) // cols
            # Resize to same size (fit to min w/h)
            min_w = min(im.width for im in imgs)
            min_h = min(im.height for im in imgs)
            norm = [ImageOps.contain(im, (min_w, min_h)) for im in imgs]
            
            # Calculate label height if needed
            label_height = 30 if label_mode != "None" else 0
            grid_w = cols * min_w + (cols - 1) * pad
            grid_h = rows * (min_h + label_height) + (rows - 1) * pad
            
            canvas = Image.new("RGB", (grid_w, grid_h), color=(255, 255, 255))
            
            # Metadata for JSON output
            metadata = {
                "grid_layout": {
                    "columns": cols,
                    "rows": rows,
                    "cell_width": min_w,
                    "cell_height": min_h,
                    "padding": pad,
                    "label_height": label_height
                },
                "images": []
            }
            
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(canvas)
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except Exception:
                font = ImageFont.load_default()
            
            for idx, (im, name) in enumerate(zip(norm, selected)):
                r = idx // cols
                c = idx % cols
                x = c * (min_w + pad)
                y = r * (min_h + label_height + pad)
                
                # Paste image
                canvas.paste(im, (x, y))
                
                # Add label below image
                label_text = ""
                if label_mode == "Filename":
                    label_text = Path(name).stem
                elif label_mode == "Custom (1, 2, 3...)" and idx < len(custom_labels):
                    label_text = custom_labels[idx]
                elif label_mode == "Autonum":
                    label_text = str(idx + 1)
                
                if label_text:
                    # Draw label text
                    text_bbox = draw.textbbox((0, 0), label_text, font=font)
                    text_w = text_bbox[2] - text_bbox[0]
                    text_h = text_bbox[3] - text_bbox[1]
                    text_x = x + (min_w - text_w) // 2
                    text_y = y + min_h + 5
                    draw.text((text_x, text_y), label_text, fill=(0, 0, 0), font=font)
                
                # Store metadata
                metadata["images"].append({
                    "index": idx,
                    "filename": name,
                    "label": label_text,
                    "position": {"x": x, "y": y, "width": min_w, "height": min_h}
                })
            
            st.image(canvas, caption=f"Grid {len(selected)} images", use_column_width=True)
            if st.button("Save Grid", key="save_grid"):
                out_dir = Path(config.get("directories.output", "./output"))
                out_dir.mkdir(parents=True, exist_ok=True)
                # 300 DPI saving hint by specifying resolution for TIFF/PNG where supported
                dest = out_dir / generate_timestamped_filename("image_grid", "png")
                try:
                    canvas.save(dest, format="PNG", dpi=(300, 300))
                    
                    # Save metadata JSON
                    import json
                    metadata_file = dest.with_suffix(".json")
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2)
                    
                    st.success(f"Saved grid: {dest.name} and metadata: {metadata_file.name}")
                except Exception as e:
                    st.error(f"Grid save failed: {e}")

