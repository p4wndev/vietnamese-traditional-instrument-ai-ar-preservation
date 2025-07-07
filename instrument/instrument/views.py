from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Img_predictions, Instrument
from ultralytics import YOLO
from owlready2 import get_ontology
import random
import cv2
import numpy as np
from numpy import argmax
import tensorflow as tf
import os
import torch
import contextlib

def create_lenet_model(input_shape=(64, 64, 3), num_classes=14):
    model = tf.keras.Sequential()

    # C1 Convolution Layer
    model.add(tf.keras.layers.Conv2D(filters=6, strides=(1,1), kernel_size=(5,5), activation='tanh', input_shape=input_shape))

    # S2 SubSampling Layer
    model.add(tf.keras.layers.AveragePooling2D(pool_size=(2,2), strides=(2,2)))

    # C3 Convolution Layer
    model.add(tf.keras.layers.Conv2D(filters=6, strides=(1,1), kernel_size=(5,5), activation='tanh'))

    # S4 SubSampling Layer
    model.add(tf.keras.layers.AveragePooling2D(pool_size=(2,2), strides=(2,2)))

    # C5 Fully Connected Layer
    model.add(tf.keras.layers.Dense(units=120, activation='tanh'))

    # Flatten the output so that we can connect it with the fully connected layers by converting it into a 1D Array
    model.add(tf.keras.layers.Flatten())

    # FC6 Fully Connected Layers
    model.add(tf.keras.layers.Dense(units=84, activation='tanh'))

    # Output Layer
    model.add(tf.keras.layers.Dense(units=num_classes, activation='softmax'))

    return model


class InstrumentList(APIView):
    def get(self, request, *args, **kwargs):
        instruments = Instrument.objects.all()
        data = []
        for instrument in instruments:
            data.append({
                'name': instrument.name,
                'description': instrument.description,
            })
        return Response(data, status=status.HTTP_200_OK)

class ImageDetectAPI(APIView):

    def post(self, request, *args, **kwargs):
        image_input = request.FILES.get('image_input')

        if not image_input:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        img = Img_predictions.objects.create(image=image_input)
        img.save()

        list_img, cl_out = self.detect_img(img.image.path)
        output = [f'predict/image_{i:03d}.jpg' for i in range(list_img)]

        return Response({'output': output, "cl_o": cl_out})

    def detect_img(self, path_img):
        @contextlib.contextmanager
        def disable_weights_only():
            original_load = torch.load
            torch.load = lambda f, *args, **kwargs: original_load(f, *args, **{**kwargs, 'weights_only': False})
            try:
                yield
            finally:
                torch.load = original_load
        
        # Sử dụng context manager khi load model YOLO
        with disable_weights_only():
            model = YOLO("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_yolo//best.pt")
        
        img_input = cv2.imread(path_img)
        if img_input is None:
            print(f"Không thể đọc ảnh: {path_img}")
            return 0, []
        
        # Lưu kích thước gốc của ảnh
        orig_h, orig_w = img_input.shape[:2]
        
        results = model.predict(source=img_input)
        results = results[0]
        
        listImg = []
        class_out = []
        
        # Kiểm tra nếu không có mask nào được phát hiện
        if results.masks is None:
            print("Không có mask nào được phát hiện trong ảnh")
            return 0, []
        
        masks = results.masks.data.cpu().numpy()
        classes = results.boxes.cls.cpu().numpy().astype(int)
        
        os.makedirs('instrument/static/predict', exist_ok=True)
        
        # Cho mỗi đối tượng
        for i, mask in enumerate(masks):
            cls_id = classes[i]
            
            # QUAN TRỌNG: Resize mask về kích thước ảnh gốc
            mask_resized = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
            
            # Tạo binary mask từ mask đã resize
            binary_mask = (mask_resized * 255).astype(np.uint8)
            
            # Áp dụng mask lên ảnh gốc
            masked_img = cv2.bitwise_and(img_input, img_input, mask=binary_mask)
            
            # Tìm bounding box nhỏ nhất chứa mask
            ys, xs = np.where(binary_mask > 0)
            if len(ys) == 0 or len(xs) == 0:
                print(f"Không tìm thấy pixel mask cho đối tượng {i}")
                continue
                
            y1, y2 = ys.min(), ys.max()
            x1, x2 = xs.min(), xs.max()
            crop = masked_img[y1:y2+1, x1:x2+1]
            
            # Lưu ảnh đã cắt (đổi thành .jpg)
            listImg.append(crop)
            cv2.imwrite(f'instrument/static/predict/image_{i:03d}.jpg', crop)
        
        # Dự đoán lớp cho từng ảnh đã cắt
        for t in range(len(listImg)):
            # Không cần chuyển đổi màu vì OpenCV mặc định là BGR
            # Để nguyên img_cut ở dạng BGR vì model LeNet cần 3 kênh màu
            label = self.predict_lenet(listImg[t])
            print(f"Label for image_{t:03d}: {label}")
            class_out.append(label)
        
        return len(listImg), class_out

    def predict_lenet(self, image):
        categories = ['cong_chieng', 'dan_bau', 'dan_co', 'dan_da', 'dan_day', 'dan_nguyet', 
                    'dan_sen', 'dan_t_rung', 'dan_tinh', 'dan_tranh', 'dan_ty_ba', 
                    'guitar', 'khen', 'trong_quan']
        
        # Tạo model với kiến trúc chính xác
        model_lenet = create_lenet_model(input_shape=(64, 64, 3), num_classes=14)
        
        # Load weights từ file
        model_lenet.load_weights("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_lenet//lenet5_model_300.h5")
        
        # Tiền xử lý ảnh
        img_input = cv2.resize(image, (64, 64))
        img_array = img_input.astype('float32') / 255.0
        
        # Chuẩn bị batch dự đoán
        img_batch = np.expand_dims(img_array, axis=0)
        
        # Thực hiện dự đoán
        pred = model_lenet.predict(img_batch)
        res = argmax(pred, axis=1)
        print(f"Predicted class index: {res[0]}")
        return categories[res[0]]

class OntologyInfoView(APIView):

    nhac_cu_dt = {
        'cong_chieng': 'cồng_chiêng',
        'dan_bau': 'đàn_bầu',
        'dan_co': 'đàn_cò',
        'dan_da': 'đàn_đá',
        'dan_day': 'đàn_đáy',
        'dan_nguyet': 'đàn_nguyệt',
        'dan_sen': 'đàn_sến',
        'dan_t_rung': 'đàn_t_rưng',
        'dan_tinh': 'đàn_tính',
        'dan_tranh': 'đàn_tranh',
        'dan_ty_ba': 'đàn_tỳ_bà',
        'guitar': 'guitar',
        'khen': 'khèn',
        'trong_quan': 'trống_quân'
    }

    thuoctinh = {
        'có_cách_chơi_là': 'Có cách chơi là ',
        'có_cấu_tạo_gồm': 'Có cấu tạo gồm ',
        'có_nguồn_gốc': 'Có nguồn gốc ',
        'có_số_dây_là': 'Có số dây là ',
        'có_tác_giả_là': 'Có tác giả là ',
        'có_tên_là': 'Có tên là ',
        'có_URL_là': 'Có URL là ',
        'xuất_hiện_ở_Việt_Nam_vào': 'Xuất hiện ở Việt Nam vào',
        'được_biểu_diễn_bởi': 'Được biểu diễn bởi',
        'được_sử_dụng_trong': 'Được sử dụng trong',
        'là_nhạc_cụ_đặc_trưng_ở': 'Là nhạc cụ đặc trưng ở',
        'được_dùng_rộng_rãi_trong_dân_tộc': 'Được sử dụng rộng rãi trong danh tộc'
    }

    def get(self, request, one_class_name):
        onto = get_ontology("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//ontology//nhaccu.owl").load()
        cl_n = self.nhac_cu_dt.get(one_class_name)

        if not cl_n:
            return Response({'error': 'Invalid class name'}, status=status.HTTP_400_BAD_REQUEST)

        dict_onto_info = {}
        video_info = []
        list_dict_video_out = []
        properties = eval(f'onto.{cl_n}.get_properties()')
        values = eval(f'onto.{cl_n}')
        for prop in properties:
            if prop.python_name == "được_sử_dụng_trong":
                nghethuat = set()
                for value in prop[values]:
                    video_info.append(value.name)
                    str = onto.get_parents_of(value)[0].name
                    nghethuat.add(str)
                S = ', '.join(nghethuat)
                S = S.replace('_',' ')
                dict_onto_info[self.thuoctinh[prop.python_name]] = S
            elif prop.python_name == "có_cấu_tạo_gồm":
                cautao = set()
                for value in prop[values]:
                    # str = onto.get_parents_of(value)[0].name
                    str = value.name
                    cautao.add(str)
                S = ', '.join(cautao)
                S = S.replace('_',' ')
                dict_onto_info[self.thuoctinh[prop.python_name]] = S
            elif prop.python_name == 'được_dùng_rộng_rãi_trong_dân_tộc':
                dantoc = set()
                for value in prop[values]:
                    str = value.name
                    dantoc.add(str)
                S = ', '.join(dantoc)
                S = S.replace('_',' ')
                dict_onto_info[self.thuoctinh[prop.python_name]]= S
            elif prop.python_name == 'là_nhạc_cụ_đặc_trưng_ở':
                khuvuc = set()
                for value in prop[values]:
                    str = value.name
                    khuvuc.add(str)
                S = ', '.join(khuvuc)
                S = S.replace('_',' ')
                dict_onto_info[self.thuoctinh[prop.python_name]]= S
            else:
                for value in prop[values]:
                    try:
                        dict_onto_info[self.thuoctinh[prop.python_name]] = value.name
                    except:
                        dict_onto_info[self.thuoctinh[prop.python_name]] = value

        if len(video_info) > 3:
            video_list = [random.choice(video_info) for _ in range(3)]
        else:
            video_list = video_info
        
        for i in video_list:
            a = eval(f'onto.{i}.get_properties()')
            b = eval(f'onto.{i}')
            dictionary = {}
            for prop in a:
                if prop.python_name != "được_sử_dụng_trong":
                    for value in prop[b]:
                        dictionary[self.thuoctinh[prop.python_name]] = value
            list_dict_video_out.append(dictionary)

        return Response({'ontology_info': dict_onto_info, 'videos': list_dict_video_out}, status=status.HTTP_200_OK)
    


# ====================================================================================
# ====================================================================================
#   RAG
# ====================================================================================
# ====================================================================================
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import openai

load_dotenv()  # Đọc file .env
# Thiết lập API key cho OpenAI
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# Đường dẫn đến FAISS VectorDB (đảm bảo đường dẫn này chính xác)
VECTOR_DB_PATH = "E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//RAG//vectorstores//db_faiss_pdf"

def load_faiss_db():
    """Tải sẵn FAISS DB sử dụng embedding từ HuggingFace."""
    embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    db = FAISS.load_local(VECTOR_DB_PATH, embedding_model, allow_dangerous_deserialization=True)
    return db

def create_prompt(template):
    """Tạo PromptTemplate từ chuỗi template."""
    return PromptTemplate(template=template, input_variables=["context", "question"])

def create_qa_chain(prompt, db):
    """Tạo chain QA với mô hình OpenAI."""
    llm = ChatOpenAI(
        model="gpt-3.5-turbo", 
        temperature=0.7,  # Điều chỉnh nhiệt độ
        max_tokens=512,  # Giới hạn số lượng token
        top_p=0.9,       # Điều chỉnh top-p
        frequency_penalty=0.5,  # Giảm lặp lại
        presence_penalty=0.6   # Giảm tái sử dụng từ
    ) # hoặc sử dụng "gpt-4"

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 5}, max_tokens_limit=1024),
        return_source_documents=True,
        chain_type_kwargs={'prompt': prompt}
    )
    return qa_chain

# ---- Load và khởi tạo các mô hình sẵn bên ngoài API ----

# Tải FAISS DB
db = load_faiss_db()

# Tạo Prompt với template
template = """
<|im_start|>system
Sử dụng thông tin sau đây để trả lời câu hỏi một cách chi tiết, rõ ràng và có giải thích. 
- Nếu bạn không biết câu trả lời, hãy nói **không biết**, đừng cố tạo ra câu trả lời.
- Khi trả lời:
  + Hãy **xuống dòng hợp lý** để dễ đọc.
  + Dùng **in đậm** cho các tiêu đề hoặc điểm chính.
  + Nếu có nhiều ý, hãy **liệt kê bằng dấu gạch đầu dòng (-)** hoặc **số thứ tự (1., 2., ...)** khi phù hợp.
  + Nếu có định nghĩa hoặc thuật ngữ, hãy làm nổi bật chúng.
{context}
<|im_end|>

<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""
prompt = create_prompt(template)

# Tạo chain QA sử dụng prompt và FAISS DB đã tải
qa_chain = create_qa_chain(prompt, db)

# ---- APIView sử dụng chain đã được tải sẵn ----

class RAGView(APIView):
    def post(self, request, *args, **kwargs):
        # Lấy câu hỏi từ request
        question = request.data.get("question")
        if not question:
            return Response({"error": "Query is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Gọi chain đã được khởi tạo sẵn với câu hỏi
            response = qa_chain.invoke({"query": question})
            answer = response.get("result", "")
            source_documents = response.get("source_documents", [])
            docs = [doc.page_content for doc in source_documents]
            return Response({
                "answer": answer,
                "sources": docs
            }, status=status.HTTP_200_OK)
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Lỗi khi gọi API RAG: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ====================================================================================
# ====================================================================================
#   END RAG
# ====================================================================================
# ====================================================================================

import os
import cv2
import contextlib
import torch
import numpy as np
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ultralytics import YOLO
from moviepy import VideoFileClip, AudioFileClip
import moviepy    
import subprocess as sp
from openai import OpenAI
import uuid

class VideoDetectView(APIView):

    @contextlib.contextmanager
    def disable_weights_only(self):
        """Temporarily disable weights_only loading restriction"""
        original_load = torch.load
        torch.load = lambda f, *args, **kwargs: original_load(f, *args, **{**kwargs, 'weights_only': False})
        try:
            yield
        finally:
            torch.load = original_load

    def post(self, request, *args, **kwargs):
        video_file = request.FILES.get('video')
        interval = int(request.data.get('interval', 1))  # Get interval with default 1 second
        
        if not video_file:
            return Response({"error": "No video provided"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate interval
        if interval <= 0:
            interval = 1
        
        # Save temporary video
        temp_path = 'temp_video.mp4'
        with open(temp_path, 'wb+') as destination:
            for chunk in video_file.chunks():
                destination.write(chunk)
        
        try:
            # Process video and get detection results
            output_video_path, time_detections = self.process_video(temp_path, interval)
            # Thêm âm thanh vào video đã xử lý
            final_output_path = self.add_audio_to_video(temp_path, output_video_path)
        except Exception as e:
            return Response({"error": f"Video processing failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        # Sử dụng video đã có âm thanh
        video_url = request.build_absolute_uri(f'/static/predict/{os.path.basename(final_output_path)}')

        generate_music_description1 = self.generate_music_description(time_detections)
        print(f"Generated music description: {generate_music_description1}")
        return Response({
            'video_url': video_url,
            'time_detections': time_detections,
            'music_description': generate_music_description1
        })

    def add_audio_to_video(self, original_video_path, processed_video_path):
        """Thêm âm thanh từ video gốc vào video đã xử lý"""
        try:
            # Tạo tên file mới cho video có âm thanh
            # final_path = processed_video_path.replace('.mp4', '_with_audio.mp4')
            unique_id = uuid.uuid4().hex
            final_path = processed_video_path.replace('.mp4', f'_{unique_id}_with_audio.mp4')
            
            # Lấy âm thanh từ video gốc
            audio_clip = AudioFileClip(original_video_path)
            
            # Lấy hình ảnh từ video đã xử lý
            video_clip = VideoFileClip(processed_video_path)
            
            # Kết hợp âm thanh với hình ảnh
            final_clip = video_clip.with_audio(audio_clip)
            final_clip.write_videofile(
                final_path,
                codec='libx264',
                audio_codec='aac',
                fps=video_clip.fps
            )
            
            # Đóng các clip để giải phóng tài nguyên
            audio_clip.close()
            video_clip.close()
            final_clip.close()
            
            # Xóa video không có âm thanh
            os.remove(processed_video_path)
            
            return final_path
        except Exception as e:
            print(f"Error adding audio: {e}")
            # Nếu không thêm được âm thanh, trả về video gốc
            return processed_video_path
        

    def process_video(self, input_path, interval):
        """Process video frame-by-frame with YOLO detection and collect time-based results"""
        os.makedirs('instrument/static/predict', exist_ok=True)
        # output_path = 'instrument/static/predict/output_video.mp4'
        unique_id = uuid.uuid4().hex
        output_path = f'instrument/static/predict/output_video_{unique_id}.mp4'
        
        # Load YOLO model
        with self.disable_weights_only():
            model = YOLO("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_yolo//best.pt")
        
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise Exception("Cannot open input video file")
        
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"Video properties: {frame_width}x{frame_height}, FPS: {fps}, Frames: {total_frames}")
        
        if fps <= 0:
            fps = 30
            print(f"Warning: Invalid FPS, using default {fps}")
        
        # Sử dụng OpenCV với codec mặc định
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        
        if not out.isOpened():
            print("Warning: Could not open video writer, trying alternative codec")
            fourcc = cv2.VideoWriter_fourcc(*'avc1')
            out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
            
        if not out.isOpened():
            raise Exception("Could not open video writer with any codec")
        
        # Initialize time-based detection tracking
        results_map = {}
        next_time = 0.0
        frame_count = 0
        
        # Process each frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Calculate current time in seconds
            current_time = frame_count / fps
            
            # Run YOLO detection
            try:
                results = model.predict(source=frame)
                result0 = results[0]
            except Exception as e:
                print(f"YOLO prediction error: {e}")
                result0 = None
            
            # Capture detections at specified intervals
            if current_time >= next_time and result0 and result0.boxes is not None:
                # Extract unique class names
                class_out = []
                for box in result0.boxes:
                    class_id = int(box.cls[0])
                    class_name = model.names[class_id]
                    class_out.append(class_name)
                
                # Store results if instruments detected
                class_out = list(set(class_out))
                if class_out:
                    results_map[next_time] = class_out
                
                # Move to next interval
                next_time += interval
            
            # Annotate frame with bounding boxes
            if result0:
                try:
                    annotated_frame = self.annotate_frame(frame.copy(), result0)
                except Exception as e:
                    print(f"Annotation error: {e}")
                    annotated_frame = frame
            else:
                annotated_frame = frame
            
            # Write processed frame
            out.write(annotated_frame)
            frame_count += 1
            
            # Hiển thị tiến trình
            if frame_count % 100 == 0:
                print(f"Processed {frame_count}/{total_frames} frames ({frame_count/total_frames*100:.1f}%)")
        
        # Release resources
        cap.release()
        out.release()
        print(f"Video saved to: {output_path}")
        
        # Prepare time-based detection results
        time_detections = []
        for time_point in sorted(results_map.keys()):
            time_detections.append({
                'time_second': time_point,
                'detected_instruments': sorted(results_map[time_point])
            })
        
        return output_path, time_detections

    def verify_video(self, video_path):
        """Check if video is playable"""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return False
        ret, frame = cap.read()
        cap.release()
        return ret

    def annotate_frame(self, frame, results):
        """Draw segmentation masks and labels on frame"""
        # Kiểm tra nếu không có detection
        if results.boxes is None or results.masks is None:
            return frame
            
        boxes = results.boxes.xyxy.cpu().numpy()
        confidences = results.boxes.conf.cpu().numpy()
        class_ids = results.boxes.cls.cpu().numpy().astype(int)
        masks = results.masks.data.cpu().numpy()
        
        # Lấy tên class từ model
        class_names = results.names
        
        # Tạo overlay để vẽ mask
        overlay = frame.copy()
        alpha = 0.5  # Độ trong suốt
        
        # Duyệt qua từng detection
        for i, (box, conf, cls_id, mask) in enumerate(zip(boxes, confidences, class_ids, masks)):
            # Resize mask về kích thước gốc
            mask_resized = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
            
            # Tạo mask nhị phân
            binary_mask = (mask_resized > 0.5).astype(np.uint8)
            
            # Tạo màu ngẫu nhiên cho mỗi class (giữ nguyên màu giữa các frame)
            color = self.generate_color(cls_id)
            
            # 1. Vẽ segmentation mask
            # Tạo ảnh màu từ mask
            colored_mask = np.zeros_like(frame)
            colored_mask[:] = color
            
            # Áp dụng mask màu lên overlay
            overlay[binary_mask == 1] = colored_mask[binary_mask == 1]
            
            # 2. Vẽ bounding box (tùy chọn, có thể bỏ nếu không cần)
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            
            # 3. Vẽ nhãn
            label = f"{class_names[cls_id]} {conf:.2f}"
            (label_width, label_height), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
            
            # Vẽ nền nhãn
            cv2.rectangle(
                frame, 
                (x1, y1 - label_height - 10),
                (x1 + label_width, y1),
                color,
                -1
            )
            
            # Vẽ text
            cv2.putText(
                frame, 
                label, 
                (x1, y1 - 10), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, 
                (0, 0, 0), 
                1
            )
        
        # Trộn overlay với frame gốc
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
        
        return frame

    # Hàm hỗ trợ tạo màu theo class_id
    def generate_color(self, class_id):
        if not hasattr(self, 'color_cache'):
            self.color_cache = {}
            
        if class_id not in self.color_cache:
            # Tạo màu ngẫu nhiên nhưng giữ nguyên giữa các lần gọi
            self.color_cache[class_id] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )
        return self.color_cache[class_id]

    def generate_music_description(self, time_detections):
        nhac_cu_dt = {
            'cong_chieng': 'cồng_chiêng',
            'dan_bau': 'đàn_bầu',
            'dan_co': 'đàn_cò',
            'dan_da': 'đàn_đá',
            'dan_day': 'đàn_đáy',
            'dan_nguyet': 'đàn_nguyệt',
            'dan_sen': 'đàn_sến',
            'dan_t_rung': 'đàn_t_rưng',
            'dan_tinh': 'đàn_tính',
            'dan_tranh': 'đàn_tranh',
            'dan_ty_ba': 'đàn_tỳ_bà',
            'guitar': 'guitar',
            'khen': 'khèn',
            'trong_quan': 'trống_quân'
        }
        """Tạo mô tả âm nhạc bằng LLM dựa trên nhạc cụ phát hiện"""
        load_dotenv()  # Đọc file .env
        # Lấy API key từ biến môi trường
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Không tìm thấy OPENAI_API_KEY trong .env")

        client = OpenAI(api_key=api_key)

        if not time_detections:
            return "Không phát hiện nhạc cụ nào trong video"
        
        lines = ["Tôi có dữ liệu các nhạc cụ xuất hiện trong video theo thời gian:"]
        for entry in time_detections:
            t = entry['time_second']
            # instrs = entry['detected_instruments']
             # Thay instrs cũ bằng mapping có dấu
            raw_instrs = entry['detected_instruments']
            instrs = [nhac_cu_dt.get(code, code) for code in raw_instrs]
                
            if len(instrs) == 1:
                instr_text = instrs[0]
            elif len(instrs) == 2:
                instr_text = f"{instrs[0]} và {instrs[1]}"
            else:
                instr_text = ', '.join(instrs[:-1]) + ' và ' + instrs[-1]
                
            lines.append(f"- Tại giây {t}: {instr_text}")

        lines.append("Hãy tạo một đoạn mô tả ngắn (3-5 câu) về loại hình âm nhạc trong video này dựa trên các nhạc cụ xuất hiện.")
        prompt = "\n".join(lines)

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Bạn là chuyên gia âm nhạc."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}")
            return "Không thể tạo mô tả âm nhạc"