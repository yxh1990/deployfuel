from nailgun.objects.serializers.base import BasicSerializer


class ClusterSettingInfoSerializer(BasicSerializer):

    fields = (
       'id',
       'cluster_id',
       'cluster_setting'
    )

class ClusterdeployMsgSerializer(BasicSerializer):
	
 	fields = (
       'id',
       'cluster_id',
       'cluster_deploymsg'
    )

class ClusterRoleStatusSerializer(BasicSerializer):

  fields= (
      'id',
      'cluster_id',
      'cluster_role',
      'role_status'
    )