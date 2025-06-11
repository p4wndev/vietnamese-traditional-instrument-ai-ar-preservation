from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
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
import os
import tensorflow as tf
from django.conf import settings


class InstrumentList(APIView):
    def get(self, request, *args, **kwargs):
        # Truy vấn tất cả các nhạc cụ từ cơ sở dữ liệu
        instruments = Instrument.objects.all()
        # Chuẩn bị dữ liệu để trả về dưới dạng JSON
        data = []
        for instrument in instruments:
            data.append({
                'name': instrument.name,
                'description': instrument.description,
            })
        # Trả về JSON response
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
            conf = ob.conf[0].item()
            img_cut = img_input[y1:y2, x1:x2]
            listImg.append(img_cut)
            cv2.imwrite(f'instrument/static/predict/image_{i:03d}.jpg', img_cut)
            i += 1

        for t in range(len(listImg)):
            a = cv2.cvtColor(listImg[t], cv2.COLOR_RGB2BGR)
            label = self.predict_lenet(a)
            # print(label)
            print(f"Label for image_{t:03d}: {label}")
            class_out.append(label)

        return i, class_out

    def predict_lenet(self, image):
        categories = ['cong_chieng', 'dan_bau', 'dan_co', 'dan_da', 'dan_day', 'dan_nguyet', 'dan_sen', 'dan_t_rung', 'dan_tinh', 'dan_tranh', 'dan_ty_ba', 'guitar', 'khen', 'trong_quan']    
        model_lenet = tf.keras.models.load_model("E://NCKH_Instrument//CODE//instrument//instrument//instrument//model//model_lenet//lenet_model30.h5")
        model_lenet.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])  # Compile the model
        img_input = cv2.resize(image, dsize=(64, 64))
        img_array = np.array(img_input)
        from tensorflow.keras.applications.resnet50 import preprocess_input
        img_batch = np.expand_dims(img_array, axis=0)
        img_preprocessed = preprocess_input(img_batch)
        pred = model_lenet(img_preprocessed)
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
    
