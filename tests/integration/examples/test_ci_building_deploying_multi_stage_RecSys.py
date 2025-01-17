import os

from testbook import testbook

from tests.conftest import REPO_ROOT
import pytest

pytest.importorskip("tensorflow")
pytest.importorskip("feast")
pytest.importorskip("faiss")
# flake8: noqa


def test_func():
    with testbook(
        REPO_ROOT
        / "examples/Building-and-deploying-multi-stage-RecSys/01-Building-Recommender-Systems-with-Merlin.ipynb",
        execute=False,
        timeout=450,
    ) as tb1:
        NUM_OF_CELLS = len(tb1.cells)
        tb1.inject(
            """
            import os
            os.environ["DATA_FOLDER"] = "/tmp/data/"
            os.system("mkdir -p /tmp/examples")
            os.environ["BASE_DIR"] = "/tmp/examples/"
            """
        )
        tb1.execute_cell(list(range(0, 25)))
        tb1.inject(
            """
                from pathlib import Path
                from merlin.datasets.ecommerce import transform_aliccp
                from merlin.io.dataset import Dataset
                import glob

                train_min = Dataset(sorted(glob.glob('/raid/data/aliccp/train/*.parquet'))[0:2])
                valid_min = Dataset(sorted(glob.glob('/raid/data/aliccp/test/*.parquet'))[0:2])

                transform_aliccp(
                    (train_min, valid_min), output_path, nvt_workflow=outputs, workflow_name="workflow"
                )
            """
        )
        tb1.execute_cell(list(range(28, NUM_OF_CELLS)))
        assert os.path.isdir("/tmp/examples/query_tower")
        assert os.path.isdir("/tmp/examples/dlrm")
        assert os.path.isdir("/tmp/examples/feature_repo")
        assert os.path.isfile("/tmp/examples/item_embeddings.parquet")
        assert os.path.isfile("/tmp/examples/feature_repo/user_features.py")
        assert os.path.isfile("/tmp/examples/feature_repo/item_features.py")

    with testbook(
        REPO_ROOT
        / "examples/Building-and-deploying-multi-stage-RecSys/02-Deploying-multi-stage-RecSys-with-Merlin-Systems.ipynb",
        execute=False,
        timeout=2400,
    ) as tb2:
        tb2.inject(
            """
            import os
            os.environ["DATA_FOLDER"] = "/tmp/data/"
            os.environ["BASE_DIR"] = "/tmp/examples/"
            """
        )
        NUM_OF_CELLS = len(tb2.cells)
        tb2.execute_cell(list(range(0, NUM_OF_CELLS - 3)))
        top_k = tb2.ref("top_k")
        outputs = tb2.ref("outputs")
        assert outputs[0] == "ordered_ids"
        tb2.inject(
            """
            import shutil
            from merlin.core.dispatch import make_df
            from merlin.models.loader.tf_utils import configure_tensorflow
            from merlin.systems.triton.utils import run_ensemble_on_tritonserver
            configure_tensorflow()
            request = make_df({"user_id_raw": [100]})
            request["user_id_raw"] = request["user_id_raw"].astype(np.int32)
            response = run_ensemble_on_tritonserver(
                "/tmp/examples/poc_ensemble", ensemble.graph.input_schema, request, outputs,  "ensemble_model"
            )
            response = [x.tolist()[0] for x in response["ordered_ids"]]
            shutil.rmtree("/tmp/examples/", ignore_errors=True)
            """
        )
        response = tb2.ref("response")
        assert len(response) == top_k

