from flask import Flask, jsonify, request
import psycopg2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求，方便前端访问

# 数据库连接配置
db_config = {
    'host': 'localhost',
    'database': 'sale_auto_simulation',
    'user': 'postgres',
    'password': 'mysecretpassword'
}


# 1. 获取IPC配置数据的接口
@app.route('/api/config', methods=['GET'])
def get_config():
    connection = None
    cursor = None

    try:
        # 使用 db_config 连接数据库
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # 第一步: 从 simulation_result 表中获取 ipcs_config_id 数组
        cursor.execute("SELECT DISTINCT ipcs_config_id FROM simulation_result")  # 获取所有不重复的 ipcs_config_id

        ipcs_config_ids = cursor.fetchall()

        if ipcs_config_ids:
            # 提取所有 ipcs_config_id 并将其展平为一个列表
            ipcs_config_ids = [id[0] for id in ipcs_config_ids]

            # 第二步: 根据 ipcs_config_id 数组中的多个 ID 从 ipc_config 表中查询 cpu, gpus, ram, ssds
            cursor.execute("""
                SELECT cpu, gpus, ram, ssds
                FROM ipc_config
                WHERE id = ANY(%s)
            """, (ipcs_config_ids,))

            result = cursor.fetchall()

            if result:
                data = [{'cpu': row[0], 'gpus': row[1], 'ram': row[2], 'ssds': row[3]} for row in result]
                return jsonify(data)  # 返回数据
            else:
                return jsonify({"error": "No matching data found in ipc_config"}), 404
        else:
            return jsonify({"error": "No ipcs_config_id found in simulation_result"}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 2. 获取控制器配置数据的接口
@app.route('/api/controller_config', methods=['GET'])
def get_controller_config():
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT controller_id, controller_version, cameras_id, image_width, image_height
            FROM controller_config
        """)
        result = cursor.fetchall()

        if result:
            data = [{
                'controller_id': row[0],
                'controller_version': row[1],
                'cameras_id': row[2],
                'image_width': row[3],
                'image_height': row[4]
            } for row in result]
            return jsonify(data)
        else:
            return jsonify({"error": "No data found"}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 3. 新建控制器配置接口
@app.route('/api/controller_config', methods=['POST'])
def add_controller_config():
    new_configs = request.get_json()

    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        for config in new_configs:
            cursor.execute("""
                INSERT INTO controller_config (
                    controller_id, controller_version, cameras_id, image_width, image_height, 
                    image_channel, capture_images_count, network_inference_count, create_time, modified_time
                ) 
                VALUES (%s, %s, %s, %s, %s, 3, 0, 0, NOW(), NOW())
            """, (
                config['controller_id'],
                config['controller_version'],
                config['cameras_id'],
                config['image_width'],
                config['image_height']
            ))

        connection.commit()
        return jsonify({"message": "Data inserted successfully"}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 4. 定拍通讯方式接口
@app.route('/api/communication_config/fixed_capture', methods=['GET'])
def get_fixed_capture_config():
    connection = None
    cursor = None

    try:
        # 使用 db_config 连接数据库
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # 第一步: 获取 communication_type=0 的 workstation_config_ids
        cursor.execute("""
            SELECT workstation_config_ids
            FROM communication_config
            WHERE communication_type = 0
        """)
        workstation_config_ids = cursor.fetchone()

        if workstation_config_ids:
            workstation_config_ids = workstation_config_ids[0]  # 获取 int4[] 数组

            # 第二步: 根据 workstation_config_ids 查询 workstation_config 中的数据
            cursor.execute("""
                SELECT controller_config_id, to_next_ws_offset, sequences_id, sequences_interval, camera_reset_time
                FROM workstation_config
                WHERE id = ANY(%s)
            """, (workstation_config_ids,))

            result = cursor.fetchall()

            if result:
                data = []

                # 根据 controller_config_id 从 controller_config 表获取 controller_id
                for row in result:
                    controller_config_id = row[0]
                    cursor.execute("""
                        SELECT controller_id
                        FROM controller_config
                        WHERE id = %s
                    """, (controller_config_id,))

                    controller_result = cursor.fetchone()

                    controller_id = controller_result[0] if controller_result else None

                    # 组装返回的数据
                    data.append({
                        'controller_config_id': controller_config_id,
                        'controller_id': controller_id,  # 返回controller_id
                        'to_next_ws_offset': row[1],
                        'sequences_id': row[2],
                        'sequences_interval': row[3],
                        'camera_reset_interval': row[4]  # camera_reset_time 从数据库查询到并返回
                    })

                return jsonify(data)  # 返回数据
            else:
                return jsonify({"error": "No matching data found in workstation_config"}), 404
        else:
            return jsonify({"error": "No workstation_config_ids found in communication_config"}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 5. 飞拍通讯方式接口
@app.route('/api/communication_config/fly_capture', methods=['GET'])
def get_fly_capture_config():
    connection = None
    cursor = None

    try:
        # 使用 db_config 连接数据库
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # 第一步: 获取 communication_type=1 的 workstation_config_ids
        cursor.execute("""
            SELECT workstation_config_ids
            FROM communication_config
            WHERE communication_type = 1
        """)
        workstation_config_ids = cursor.fetchone()

        if workstation_config_ids:
            workstation_config_ids = workstation_config_ids[0]  # 获取 int4[] 数组

            # 第二步: 根据 workstation_config_ids 查询 workstation_config 中的数据
            cursor.execute("""
                SELECT controller_config_id, to_next_ws_offset, sequences_id, sequences_interval
                FROM workstation_config
                WHERE id = ANY(%s)
            """, (workstation_config_ids,))

            result = cursor.fetchall()

            if result:
                data = []

                # 根据 controller_config_id 从 controller_config 表获取 controller_id
                for row in result:
                    controller_config_id = row[0]
                    cursor.execute("""
                        SELECT controller_id
                        FROM controller_config
                        WHERE id = %s
                    """, (controller_config_id,))

                    controller_result = cursor.fetchone()

                    controller_id = controller_result[0] if controller_result else None

                    # 组装返回的数据
                    data.append({
                        'controller_config_id': controller_config_id,
                        'controller_id': controller_id,  # 返回controller_id
                        'to_next_ws_offset': row[1],
                        'sequences_id': row[2],
                        'sequences_interval': row[3],
                    })

                return jsonify(data)  # 返回数据
            else:
                return jsonify({"error": "No matching data found in workstation_config"}), 404
        else:
            return jsonify({"error": "No workstation_config_ids found in communication_config"}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# 6. 飞拍工作站配置接口
@app.route('/api/workstation_config/fly_capture', methods=['POST'])
def add_workstation_config_fly_capture():
    new_configs = request.get_json()
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # 获取 controller_id
        controller_id = new_configs['controller_id']

        # 根据 controller_id 获取 controller_config 的 id
        cursor.execute("""
            SELECT id
            FROM controller_config
            WHERE controller_id = %s
        """, (controller_id,))

        controller_config_result = cursor.fetchone()

        if controller_config_result:
            controller_config_id = controller_config_result[0]
            print(controller_config_id)
            # 插入到 workstation_config 表
            cursor.execute("""
                INSERT INTO workstation_config (
                    workstation_id,
                    controller_config_id, 
                    to_next_ws_offset, 
                    camera_reset_time,
                    sequence_count,
                    sequences_id, 
                    sequences_interval,
                    create_time,
                    modified_time
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                9,
                controller_config_id,  # 已获取的 controller_config_id
                int(new_configs['to_next_ws_offset']),
                3,  # 这里你设置 camera_reset_time 为 3，如果有不同的要求请修改
                len(new_configs['sequences_interval']),
                [int(new_configs['sequence_count'])],  # 将 sequence_count 作为 sequences_id
                new_configs['sequences_interval']  # 处理为数组存储
            ))

        connection.commit()
        return jsonify({"message": "Workstation config inserted successfully"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

# 7. 定拍工作站配置接口
@app.route('/api/workstation_config/fixed_capture', methods=['POST'])
def add_workstation_config_fixed_capture():
    new_configs = request.get_json()
    connection = None
    cursor = None

    try:
        connection = psycopg2.connect(**db_config)
        cursor = connection.cursor()

        # 获取 controller_id
        controller_id = new_configs['controller_id']

        # 根据 controller_id 获取 controller_config 的 id
        cursor.execute("""
            SELECT id
            FROM controller_config
            WHERE controller_id = %s
        """, (controller_id,))

        controller_config_result = cursor.fetchone()

        if controller_config_result:
            controller_config_id = controller_config_result[0]
            print(controller_config_id)
            # 插入到 workstation_config 表
            cursor.execute("""
                INSERT INTO workstation_config (
                    workstation_id,
                    controller_config_id, 
                    to_next_ws_offset, 
                    camera_reset_time,
                    sequence_count,
                    sequences_id, 
                    sequences_interval,
                    create_time,
                    modified_time
                ) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (
                9,
                controller_config_id,  # 已获取的 controller_config_id
                int(new_configs['to_next_ws_offset']),
                int(new_configs['camera_reset_interval']),
                len(new_configs['sequences_interval']),
                [int(new_configs['sequence_count'])],  # 将 sequence_count 作为 sequences_id
                new_configs['sequences_interval']  # 处理为数组存储
            ))

        connection.commit()
        return jsonify({"message": "Workstation config inserted successfully"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
