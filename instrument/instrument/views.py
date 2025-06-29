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
    model = tf.keras.Sequential([
        # Lớp Convolution đầu tiên
        tf.keras.layers.Conv2D(
            filters=32, 
            kernel_size=(5, 5), 
            padding='same', 
            activation='relu', 
            input_shape=input_shape,
            name='conv2d_1'
        ),
        
        # Lớp Max Pooling
        tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=2),
        
        # Lớp Convolution thứ hai
        tf.keras.layers.Conv2D(
            filters=48, 
            kernel_size=(5, 5), 
            padding='valid', 
            activation='relu',
            name='conv2d_2'
        ),
        
        # Lớp Max Pooling thứ hai
        tf.keras.layers.MaxPooling2D(pool_size=(2, 2), strides=2),
        
        # Làm phẳng đầu vào
        tf.keras.layers.Flatten(),
        
        # Lớp Dense 256
        tf.keras.layers.Dense(256, activation='relu'),
        
        # Lớp Dense 84
        tf.keras.layers.Dense(84, activation='relu'),
        
        # Lớp đầu ra
        tf.keras.layers.Dense(num_classes, activation='softmax')
    ])
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
        # Context manager để tạm thời vô hiệu hóa weights_only
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
        rs = model.predict(source=img_input)
        rs = rs[0]
        i = 0
        listImg = []
        class_out = []
        for ob in rs.boxes:
            box = ob.xyxy[0].tolist()
            box = [round(x) for x in box]
            x1, y1, x2, y2 = box
            img_cut = img_input[y1:y2, x1:x2]
            listImg.append(img_cut)
            os.makedirs('instrument/static/predict', exist_ok=True)
            cv2.imwrite(f'instrument/static/predict/image_{i:03d}.jpg', img_cut)
            i += 1

        for t in range(len(listImg)):
            a = cv2.cvtColor(listImg[t], cv2.COLOR_BGR2RGB)  # Sửa từ RGB2BGR thành BGR2RGB
            label = self.predict_lenet(a)
            print(f"Label for image_{t:03d}: {label}")
            class_out.append(label)

        return i, class_out

    def predict_lenet(self, image):
        categories = ['cong_chieng', 'dan_bau', 'dan_co', 'dan_da', 'dan_day', 'dan_nguyet', 
                    'dan_sen', 'dan_t_rung', 'dan_tinh', 'dan_tranh', 'dan_ty_ba', 
                    'guitar', 'khen', 'trong_quan']
        
        # Tạo model với kiến trúc chính xác
        model_lenet = create_lenet_model(input_shape=(64, 64, 3), num_classes=14)
        
        # Load weights từ file
        model_lenet.load_weights("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_lenet//lenet_model30.h5")
        
        # Tiền xử lý ảnh
        img_input = cv2.resize(image, (64, 64))
        img_array = img_input.astype('float32') / 255.0
        
        # Chuẩn bị batch dự đoán
        img_batch = np.expand_dims(img_array, axis=0)
        
        # Thực hiện dự đoán
        pred = model_lenet.predict(img_batch)
        res = argmax(pred, axis=1)
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
import tempfile, os, cv2

class VideoDetectView(APIView):
    """
    Optimized version that processes every N seconds
    """
    def post(self, request, format=None):
        video_file = request.FILES.get('video')
        interval = int(request.data.get('interval', 1))  # Process every N seconds
        
        if not video_file:
            return Response({'error': 'No video file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        @contextlib.contextmanager
        def disable_weights_only():
            original_load = torch.load
            torch.load = lambda f, *args, **kwargs: original_load(f, *args, **{**kwargs, 'weights_only': False})
            try:
                yield
            finally:
                torch.load = original_load

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        try:
            with open(temp_file.name, 'wb') as f:
                for chunk in video_file.chunks():
                    f.write(chunk)

            with disable_weights_only():
                image_detector = ImageDetectAPI()
                image_detector.model = YOLO("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_yolo//best.pt")

            cap = cv2.VideoCapture(temp_file.name)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                fps = 30
                
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            results_map = {}
            
            # Process every 'interval' seconds
            current_time = 0
            while current_time < duration:
                target_frame = int(current_time * fps)
                
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                print(f"Processing time {current_time}s, frame {target_frame}")
                
                # Direct detection on frame
                results = image_detector.model(frame)
                
                class_out = []
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            class_id = int(box.cls[0])
                            class_name = image_detector.model.names[class_id]
                            class_out.append(class_name)
                
                if class_out:
                    results_map[current_time] = list(set(class_out))
                    
                current_time += interval

            cap.release()

            output = []
            for time_point in sorted(results_map):
                output.append({
                    'time_second': time_point,
                    'detected_instruments': sorted(results_map[time_point])
                })
            
            return Response(output)

        except Exception as e:
            return Response({'error': f'Error processing video: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        finally:
            try:
                os.remove(temp_file.name)
            except OSError:
                pass

