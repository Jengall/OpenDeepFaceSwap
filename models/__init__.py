from .BaseTypes import TrainingDataType
from .BaseTypes import TrainingDataSample

from .ModelBase import ModelBase
from .ConverterBase import ConverterBase
from .ConverterMasked import ConverterMasked
from .ConverterAvatar import ConverterAvatar
from .TrainingDataGeneratorBase import TrainingDataGeneratorBase
from .FaceTrainingDataGenerator import FaceTrainingDataGenerator
from .ImageTrainingDataGenerator import ImageTrainingDataGenerator

def import_model(name):
    module = __import__('Model_'+name, globals(), locals(), [], 1)
    return getattr(module, 'Model')