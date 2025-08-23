from fastapi import APIRouter, Depends, Form, Request, BackgroundTasks
from pydantic_validation_decorator import ValidateFields
from sqlalchemy.ext.asyncio import AsyncSession
from config.enums import BusinessType
from config.get_db import get_db
from module_admin.annotation.log_annotation import Log
from module_admin.aspect.interface_auth import CheckUserInterfaceAuth
from module_admin.entity.vo.user_vo import CurrentUserModel
from module_admin.service.login_service import LoginService
from module_algo.task.service.task_service import TaskService
from module_algo.container.service.container_service import ContainerService
from module_algo.task.entity.vo.task_vo import DeleteTaskModel, TaskModel, TaskPageQueryModel
from utils.common_util import bytes2file_response
from utils.log_util import logger
from utils.page_util import PageResponseModel
from utils.response_util import ResponseUtil
import httpx
import json
import io
import uuid
import zipfile
from pathlib import Path
from typing import List, Dict, Union
from datetime import datetime
from module_algo.file.entity.do.file_do import File
from module_algo.file.service.file_service import FileService


taskController = APIRouter(prefix='/task/task', dependencies=[Depends(LoginService.get_current_user)])


@taskController.get(
    '/list', response_model=PageResponseModel, dependencies=[Depends(CheckUserInterfaceAuth('task:task:list'))]
)
async def get_task_task_list(
    request: Request,
    task_page_query: TaskPageQueryModel = Depends(TaskPageQueryModel.as_query),
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    dept_id = current_user.user.dept_id
    task_page_query.dept = dept_id
    # 获取分页数据
    task_page_query_result = await TaskService.get_task_list_services(query_db, task_page_query, is_page=True, dept_id=dept_id)
    logger.info('获取成功')

    return ResponseUtil.success(model_content=task_page_query_result)


@taskController.post('', dependencies=[Depends(CheckUserInterfaceAuth('task:task:add'))])
@ValidateFields(validate_model='add_task')
@Log(title='任务', business_type=BusinessType.INSERT)
async def add_task_task(
    request: Request,
    add_task: TaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    dept_id = current_user.user.dept_id
    add_task.dept = dept_id
    add_task_result = await TaskService.add_task_services(query_db, add_task)
    logger.info(add_task_result.message)

    return ResponseUtil.success(msg=add_task_result.message)


@taskController.put('', dependencies=[Depends(CheckUserInterfaceAuth('task:task:edit'))])
@ValidateFields(validate_model='edit_task')
@Log(title='任务', business_type=BusinessType.UPDATE)
async def edit_task_task(
    request: Request,
    edit_task: TaskModel,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
):
    dept_id = current_user.user.dept_id
    edit_task.dept = dept_id
    edit_task_result = await TaskService.edit_task_services(query_db, edit_task)
    logger.info(edit_task_result.message)

    return ResponseUtil.success(msg=edit_task_result.message)


@taskController.delete('/{ids}', dependencies=[Depends(CheckUserInterfaceAuth('task:task:remove'))])
@Log(title='任务', business_type=BusinessType.DELETE)
async def delete_task_task(request: Request, ids: str, query_db: AsyncSession = Depends(get_db),
current_user: CurrentUserModel = Depends(LoginService.get_current_user)):
    dept_id = current_user.user.dept_id
    delete_task = DeleteTaskModel(ids=ids)
    delete_task_result = await TaskService.delete_task_services(query_db, delete_task, dept_id)
    logger.info(delete_task_result.message)

    return ResponseUtil.success(msg=delete_task_result.message)


@taskController.get(
    '/{id}', response_model=TaskModel, dependencies=[Depends(CheckUserInterfaceAuth('task:task:query'))]
)
async def query_detail_task_task(request: Request, id: int, query_db: AsyncSession = Depends(get_db)):
    task_detail_result = await TaskService.task_detail_services(query_db, id)
    logger.info(f'获取id为{id}的信息成功')

    return ResponseUtil.success(data=task_detail_result)


@taskController.post(
    "/stop",
    dependencies=[Depends(CheckUserInterfaceAuth('task:task:remove'))]
    )
async def stop_task(
    task_id: int,
    query_db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user)
):
    """
    停止指定任务
    """
    dept_id = current_user.user.dept_id
    # 获取容器信息
    task = await TaskService.task_detail_services(query_db, task_id)
    if task.dept != dept_id:
        logger.warning(f'任务不存在: {task_id}')
        return ResponseUtil.failure(msg="任务不存在")

    if task.state not in ['running', 'pending']:
            return ResponseUtil.failure(msg=f"任务当前状态为{task.state}，无需停止")

    container = await ContainerService.container_detail_services(query_db, task.container)
    if container.dept != dept_id:
        logger.warning(f'容器不存在: {container.id}')
        return ResponseUtil.failure(msg="容器不存在")
    # 转发请求到容器服务
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                        f"{container.url}/stop", 
                        data={"task_id": task_id},
                        headers={"Content-Type": "application/x-www-form-urlencoded"}
                    )
            response.raise_for_status()
            if response.status_code == 200:
                task.state = "stop"
                await query_db.commit()
                return ResponseUtil.success(data={"message": "任务停止成功"})
    except Exception as e: # 假设服务器错误或其他httpx错误不会导致404，因此直接捕获Exception
        logger.error(f'任务停止失败: {str(e)}')
        return ResponseUtil.failure(msg=f"任务停止失败: {str(e)}")




async def process_invocation(
        db: AsyncSession,
        client: httpx.AsyncClient,
        root: int,
        name: str,
        args: Dict[str, Union[List[int], float, str]],
        dept_id: int):
    """
    处理单个算法调用的核心逻辑
    参数：
    - db: 数据库会话对象
    - client: 复用HTTP客户端实例
    - args: 单个调用的参数字典
    - dept_id: 发起请求的用户部门
    """
    file_ids = args["file_ids"]
    del args["file_ids"]

    file_records = await FileService.file_detail_services(db, file_ids)
    if len(file_records) != len(file_ids):
        logger.warning(f'部分文件不存在: {file_ids}')
        return ResponseUtil.failure(msg="部分文件不存在")
    # 创建临时压缩文件
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_record in file_records:
            # 添加文件到压缩包
            with open(Path(file_record.path), "rb") as f:
                file_data = f.read()
            zip_file.writestr(file_record.name, file_data)

    task_id = args["task_id"]
    del args["task_id"]

    task = await TaskService.task_detail_services(db, task_id)
    if not task or task.dept != dept_id:
        logger.warning(f'Task with id {task_id} not found')
        return ResponseUtil.failure(msg="任务不存在")

    container = await ContainerService.container_detail_services(db, task.container)
    if not container or container.dept != dept_id:
        logger.warning(f'Container with id {task.container} not found')
        return ResponseUtil.failure(msg="容器不存在")
    url = container.url
    algo = task.algo

    zip_buffer.seek(0)

    try:
        # 发送压缩文件请求
        response = await client.post(
            f'{url}/process',
            files={"file": ("input_files.zip", zip_buffer, "application/zip")},
            data={"task_id": str(task_id), "algo_name": algo, "args_json": json.dumps(args)}
        )
        response.raise_for_status()

        # 创建结果目录
        result_dir = Path("./file_uploads/results") / str(uuid.uuid4())
        result_dir.mkdir(parents=True, exist_ok=True)

        # 保存返回文件到目录（假设返回的是zip）
        with zipfile.ZipFile(io.BytesIO(response.content)) as response_zip:
            response_zip.extractall(result_dir)

        # 创建目录记录
        dir_record = File(
            name=name,
            path=str(result_dir),
            root=root,
            type="dir",
            upload_time=datetime.now(),
            dept = dept_id
        )

        db.add(dir_record)
        await db.commit()
        await db.refresh(dir_record)

        # 创建文件记录（如果需要记录单个文件）
        for file_path in result_dir.iterdir():
                file_record = File(
                    name=file_path.name,
                    path=str(file_path),
                    root=dir_record.id,
                    type=file_path.suffix[1:] if file_path.suffix else "unknown",
                    upload_time=datetime.now(),
                    dept = dept_id,
                    size=file_path.stat().st_size,
                )
                db.add(file_record)
        await db.commit()

        await db.refresh(dir_record)
        return dir_record.id

    except Exception as e:
        await db.rollback()
        raise e


async def background_processor(db: AsyncSession, task_id: int, dept_id: int, args: List[Dict[str, Union[List[int], float, str]]]):
    """
    后台任务处理器
    参数：
    - task_id: 任务ID
    - args: 参数列表
    """

    try:

        task = await TaskService.task_detail_services(db, task_id)
        if task.state == 'running':
            logger.info(f'Task {task_id} is already running')
            return

        task.state = 'running'

        await db.commit()

        # 使用异步事务
        dir_record = File(
                filename=task.name,
                root=1,
                file_type="dir",
                upload_time=datetime.now(),
                dept = dept_id
            )
        db.add(dir_record)
        await db.commit()
        await db.refresh(dir_record)

        i = 0

        # 使用异步HTTP客户端（保持连接池复用）
        async with httpx.AsyncClient() as client:
            for arg in args:
                i = i+1
                arg['task_id'] = task_id
                file = await process_invocation(db, client, dir_record.id, f"{task.name}---{i}", arg, dept_id)

        # 任务完成后，更新任务状态
        task.state = 'success'
        task.end_time = datetime.now()
        task.result = dir_record.id
        await db.commit()
        await db.refresh(task)

    except Exception as e:
        task = await TaskService.task_detail_services(db, task_id)
        task.state = 'failed'
        await db.commit()
        raise e





@taskController.post("/process", dependencies=[Depends(CheckUserInterfaceAuth('task:task:remove'))])
@Log(title='任务处理', business_type=BusinessType.OTHER)
async def process_task(
    request: Request,
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUserModel = Depends(LoginService.get_current_user),
    ):
    """
    处理任务端点
    流程：
    1. 校验任务、算法和容器是否存在
    2. 提取用户身份
    3. 提交后台任务处理
    4. 立即返回响应
    """
        # 校验任务是否存在
    dept_id = current_user.user.dept_id
    task = await TaskService.task_detail_services(db, task_id)
    if not task or task.dept != dept_id:
        logger.warning(f'任务不存在或无权访问: {task_id}')
        return ResponseUtil.failure(msg="任务不存在或无权访问")
    
    container_id = task.container
    # 校验容器是否存在
    container = await ContainerService.container_detail_services(db, container_id)
    if not container or not container.url or container.dept != dept_id:
        logger.warning(f'容器不存在、无效或无权访问: {container_id}')
        return ResponseUtil.failure(msg="容器不存在、无效或无权访问")

    try:
        # 解析参数JSON
        args: List[Dict[str, Union[List[int], float, str]]] = json.loads(task.args)
        background_tasks.add_task(background_processor, db, dept_id, task_id, args)
    except json.JSONDecodeError:
        logger.error(f'参数格式无效: {task_id}')
        return ResponseUtil.failure(msg="参数格式无效，必须是JSON字符串")
    except Exception as e:
        logger.error(f'处理任务失败: {str(e)}')
        return ResponseUtil.failure(msg=f'处理任务失败: {str(e)}')

    logger.info(f'任务已提交，正在处理中: {task_id}')
    return ResponseUtil.success(
        msg="任务已提交，正在处理中",
        data={"task_id": task_id}
    )

