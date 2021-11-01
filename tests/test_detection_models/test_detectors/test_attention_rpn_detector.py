# Copyright (c) OpenMMLab. All rights reserved.

import copy

import pytest
import torch

from mmfewshot.detection.models import build_detector
from .test_fine_tune_based_detector import _get_detector_cfg


@pytest.mark.parametrize(
    'cfg_file',
    [
        'detection/attention_rpn/voc/split1/attention-rpn_r50_c4_voc-split1_base-training.py',  # noqa
        'detection/attention_rpn/voc/split1/attention-rpn_r50_c4_voc-split1_1shot-fine-tuning.py'  # noqa
    ])
def test_attention_rpn_detector_forward(cfg_file):
    if not torch.cuda.is_available():
        import pytest
        pytest.skip('test requires GPU and torch+cuda')
    model = _get_detector_cfg(cfg_file)
    model.backbone.init_cfg = None
    model.roi_head.shared_head.pretrained = None
    model.rpn_head.num_support_shots = 2
    model.roi_head.num_support_shots = 2
    model = build_detector(model)
    gt_bboxes = [
        torch.Tensor([[23.6667, 23.8757, 238.6326, 151.8874]]),
    ]
    # test train forward
    query_data = dict(
        img_metas=[{
            'img_shape': (256, 256, 3),
            'scale_factor': 1,
            'pad_shape': (256, 256, 3)
        }],
        img=torch.randn(1, 3, 256, 256),
        gt_bboxes=copy.deepcopy(gt_bboxes),
        gt_labels=[torch.LongTensor([0])],
        query_class=torch.LongTensor([0]))
    support_data = dict(
        img_metas=[{
            'img_shape': (320, 320, 3),
            'scale_factor': 1,
            'pad_shape': (320, 320, 3)
        }] * 4,
        img=torch.randn(4, 3, 320, 320),
        gt_bboxes=copy.deepcopy(gt_bboxes) * 4,
        gt_labels=[
            torch.LongTensor([0]),
            torch.LongTensor([0]),
            torch.LongTensor([1]),
            torch.LongTensor([1])
        ],
    )
    model.train()
    losses = model(
        query_data=query_data, support_data=support_data, mode='train')
    assert 'loss_rpn_cls' in losses
    assert 'loss_rpn_bbox' in losses
    assert 'loss_cls' in losses
    assert 'acc' in losses
    assert 'loss_bbox' in losses
    data_init = dict(
        img_metas=[{
            'img_shape': (320, 320, 3),
            'scale_factor': 1,
            'pad_shape': (320, 320, 3)
        }] * 5,
        img=torch.randn(5, 3, 320, 320),
        gt_bboxes=copy.deepcopy(gt_bboxes) * 5,
        gt_labels=[torch.LongTensor([i]) for i in range(5)],
    )
    with torch.no_grad():
        model(**data_init, mode='model_init')
        results = model(
            img_metas=[[{
                'img_shape': (256, 256, 3),
                'scale_factor': 1,
                'pad_shape': (256, 256, 3)
            }]],
            img=[torch.randn(1, 3, 256, 256)],
            mode='test')
        assert len(results) == 1
        assert len(results[0]) == 5