#include<rclcpp/rclcpp.hpp>
#include<rclcpp_lifecycle/lifecycle_node.hpp>
#include<std_msgs/msg/string.hpp>

#include<memory>
#include<thread>

using std::placeholders::_1;
using namespace std::chrono_literals;


class SimpleLifecycleNode : public rclcpp_lifecycle::LifecycleNode
{
    public:
    // Construct the lifecycle node and optionally enable intra-process communications.
    explicit SimpleLifecycleNode(const std::string & node_name, bool intra_process_comes = false)
    : rclcpp_lifecycle::LifecycleNode(node_name, rclcpp::NodeOptions().use_intra_process_comms(intra_process_comes))
    {

    }

    // Configure state callback: subscribe to the chatter topic.
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_configure(const rclcpp_lifecycle::State &)
    {
        sub_ = create_subscription<std_msgs::msg::String>("chatter", 10, std::bind(&SimpleLifecycleNode::msgCallback, this, _1));
        RCLCPP_INFO(get_logger(), "Lifecycle Node on_configure() called");
        return  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    // Shutdown state callback: release resources.
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_shutdown(const rclcpp_lifecycle::State &)
    {
        sub_.reset();
        RCLCPP_INFO(get_logger(), "Lifecycle Node on_shutdown() called");
        return  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    // Cleanup state callback: reset the subscription.
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_cleanup(const rclcpp_lifecycle::State &)
    {
        sub_.reset();
        RCLCPP_INFO(get_logger(), "Lifecycle Node on_cleanup() called");
        return  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    // Activate state callback: transition to active and simulate work.
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_activate(const rclcpp_lifecycle::State & state)
    {
        LifecycleNode::on_activate(state);
        RCLCPP_INFO(get_logger(), "Lifecycle Node on_activate() called");
        std::this_thread::sleep_for(2s);
        return  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    // Deactivate state callback: transition back to inactive.
    rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn on_deactivate(const rclcpp_lifecycle::State & state)
    {
        LifecycleNode::on_deactivate(state);
        RCLCPP_INFO(get_logger(), "Lifecycle Node on_deactivate() called");
        return  rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn::SUCCESS;
    }

    // Only log incoming messages when the node is in the active state.
    void msgCallback(const std_msgs::msg::String & msg)
    {
        auto state = get_current_state();
        if(state.label() == "active")
        {
            RCLCPP_INFO_STREAM(get_logger(), "Lifecycle node heard : " << msg.data.c_str());
        }
    }

    private:
        rclcpp::Subscription<std_msgs::msg::String>::SharedPtr sub_;
};

// Program entry point: spin the lifecycle node using a SingleThreadedExecutor.
int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::executors::SingleThreadedExecutor ste;
    std::shared_ptr<SimpleLifecycleNode> simple_lifecycle_node =
     std::make_shared<SimpleLifecycleNode>("simple_lifecycle_node");
     
    ste.add_node(simple_lifecycle_node->get_node_base_interface());
    ste.spin();
    rclcpp::shutdown();
    return 0;
}
