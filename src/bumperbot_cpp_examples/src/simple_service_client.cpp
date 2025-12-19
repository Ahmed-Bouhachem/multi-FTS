// Minimal service client example: calls AddTwoInts with CLI-provided integers.
#include <rclcpp/rclcpp.hpp>
#include <bumperbot_msgs/srv/add_two_ints.hpp>
#include <chrono>
#include <memory>
using namespace std::placeholders;

class SimpleServiceClient : public rclcpp::Node {
    public:
        // Construct the service client node and immediately call AddTwoInts with the given operands.
        SimpleServiceClient(int a, int b) : Node("simple_service_cerver")

        {
            client_ = create_client<bumperbot_msgs::srv::AddTwoInts>("add_two_ints");

            auto request = std::make_shared<bumperbot_msgs::srv::AddTwoInts::Request>();
            request->a = a;
            request->b = b;

            while(!client_->wait_for_service(std::chrono::seconds(1))) 
            {
                if(!rclcpp::ok()) 
                {
                    RCLCPP_ERROR(get_logger(), "Interrupted while waiting for the service");
                    return;
                }
                RCLCPP_INFO(get_logger(), "Service not available, waiting again...");
            }
            // Dispatch request asynchronously and bind response handler
            auto result = client_->async_send_request(
                request,
                std::bind(&SimpleServiceClient::responseCallback, this, _1));
        }

    
    private:
        rclcpp::Client<bumperbot_msgs::srv::AddTwoInts>::SharedPtr client_;

        // Handle service response (or failure)
        void responseCallback(rclcpp::Client<bumperbot_msgs::srv::AddTwoInts>::SharedFuture future)
        {
            if(future.valid()) 
            {
                RCLCPP_INFO_STREAM(get_logger(), "Service Response" << future.get()->sum);
            } else {
                RCLCPP_ERROR(get_logger(), "Service Failure");
            }
        }
};

// Entrypoint: parse 2 integers and call the service
int main(int argc, char* argv[])
{   rclcpp::init(argc, argv);
    if(argc != 3) {
        RCLCPP_ERROR(rclcpp::get_logger("rclcpp"), "wrong number of arguments ! Usage : Simple_service_client A B");
        return 1;
    }
    auto node = std::make_shared<SimpleServiceClient>(atoi(argv[1]),atoi(argv[2]));
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
};
